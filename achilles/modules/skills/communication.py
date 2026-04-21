"""
Communication Skill
===================

Provides outbound communication capabilities via external APIs:

- **send_email**        – SMTP relay or transactional-email API (e.g. SendGrid)
- **send_message**      – Slack / Microsoft Teams / generic webhook
- **send_notification** – Fire-and-forget webhook notification

Configuration keys (``api_config``)::

    {
        "smtp_host":       "smtp.example.com",
        "smtp_port":       587,
        "smtp_user":       "user@example.com",
        "smtp_password":   "...",
        "smtp_from":       "agent@example.com",
        "sendgrid_key":    "SG...",        # alternative to SMTP
        "slack_webhook":   "https://hooks.slack.com/...",
        "teams_webhook":   "https://outlook.office.com/webhook/...",
        "default_webhook": "https://..."   # generic fallback
    }

When API credentials are absent, every action logs the intent and returns a
dry-run receipt so the agent can operate safely during development.
"""

from __future__ import annotations

import json
import logging
import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Callable, Dict, List, Optional

from achilles.modules.skills import Skill

logger = logging.getLogger(__name__)


class CommunicationSkill(Skill):
    """Outbound communication skill (email, messaging, notifications)."""

    name: str = "communication"
    description: str = (
        "Send emails, post messages to Slack/Teams, and fire webhook notifications."
    )

    def _build_action_map(self) -> Dict[str, Callable]:
        return {
            "send_email": self._send_email,
            "send_message": self._send_message,
            "send_notification": self._send_notification,
        }

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    async def _send_email(
        self,
        to: str | List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Send an email.

        Args:
            to:          Recipient address or list of addresses.
            subject:     Email subject line.
            body:        Plain-text body.
            html_body:   Optional HTML version of the body.
            cc:          Optional CC recipients.
            attachments: Optional list of ``{"filename": str, "content": bytes}``.

        Returns:
            Receipt dict with status and timestamp.
        """
        recipients = [to] if isinstance(to, str) else to
        sendgrid_key = self.api_config.get("sendgrid_key")
        smtp_host = self.api_config.get("smtp_host")

        if sendgrid_key:
            return await self._send_via_sendgrid(
                recipients, subject, body, html_body, cc, attachments
            )
        elif smtp_host:
            return await self._send_via_smtp(
                recipients, subject, body, html_body, cc
            )
        else:
            # Dry-run: log and return receipt
            logger.info(
                "[DRY-RUN] Email to=%s subject='%s'", recipients, subject
            )
            return self._receipt("send_email", "dry_run", {"to": recipients, "subject": subject})

    async def _send_via_sendgrid(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html_body: Optional[str],
        cc: Optional[List[str]],
        attachments: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Send email through the SendGrid API."""
        try:
            import aiohttp  # already a project dependency
        except ImportError:  # pragma: no cover
            return self._receipt("send_email", "error", {"reason": "aiohttp not installed"})

        key = self.api_config["sendgrid_key"]
        sender = self.api_config.get("smtp_from", "agent@nuclear-vortex.dev")

        payload: Dict[str, Any] = {
            "personalizations": [
                {
                    "to": [{"email": r} for r in recipients],
                    **({"cc": [{"email": c} for c in cc]} if cc else {}),
                }
            ],
            "from": {"email": sender},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}],
        }
        if html_body:
            payload["content"].append({"type": "text/html", "value": html_body})

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                data=json.dumps(payload),
            ) as resp:
                status = "sent" if resp.status == 202 else "error"
                return self._receipt(
                    "send_email", status, {"to": recipients, "http_status": resp.status}
                )

    async def _send_via_smtp(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html_body: Optional[str],
        cc: Optional[List[str]],
    ) -> Dict[str, Any]:
        """Send email through SMTP."""
        host = self.api_config["smtp_host"]
        port = int(self.api_config.get("smtp_port", 587))
        user = self.api_config.get("smtp_user", "")
        password = self.api_config.get("smtp_password", "")
        sender = self.api_config.get("smtp_from", user)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)
        if cc:
            msg["Cc"] = ", ".join(cc)

        msg.attach(MIMEText(body, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        all_recipients = recipients + (cc or [])
        context = ssl.create_default_context()

        try:
            with smtplib.SMTP(host, port) as server:
                server.ehlo()
                server.starttls(context=context)
                if user and password:
                    server.login(user, password)
                server.sendmail(sender, all_recipients, msg.as_string())
            return self._receipt("send_email", "sent", {"to": recipients})
        except Exception as exc:
            logger.error("SMTP send failed: %s", exc)
            return self._receipt("send_email", "error", {"reason": str(exc)})

    async def _send_message(
        self,
        text: str,
        platform: str = "slack",
        recipient: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Post a message to Slack or Microsoft Teams.

        Args:
            text:      Message text (supports Slack mrkdwn / Teams markdown).
            platform:  ``"slack"`` or ``"teams"``.
            recipient: Optional @ mention or channel name (platform-specific).
            channel:   Slack channel override (e.g. ``"#general"``).

        Returns:
            Receipt dict.
        """
        webhook_key = f"{platform.lower()}_webhook"
        webhook_url = self.api_config.get(webhook_key)

        if not webhook_url:
            logger.info(
                "[DRY-RUN] Message platform=%s text='%s'", platform, text[:60]
            )
            return self._receipt(
                "send_message", "dry_run", {"platform": platform, "text": text}
            )

        if platform.lower() == "slack":
            payload = {"text": text}
            if channel:
                payload["channel"] = channel
        else:  # teams
            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "text": text,
            }

        return await self._post_webhook(webhook_url, payload, "send_message")

    async def _send_notification(
        self,
        message: str,
        channel: str = "default",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Fire a generic webhook notification.

        Args:
            message:  Notification body text.
            channel:  Logical channel name; mapped to a webhook URL via
                      ``api_config["webhooks"][channel]`` or
                      ``api_config["default_webhook"]``.
            metadata: Optional extra data included in the payload.

        Returns:
            Receipt dict.
        """
        webhooks: Dict[str, str] = self.api_config.get("webhooks", {})
        url = webhooks.get(channel) or self.api_config.get("default_webhook")

        payload = {
            "message": message,
            "channel": channel,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **(metadata or {}),
        }

        if not url:
            logger.info("[DRY-RUN] Notification channel=%s msg='%s'", channel, message)
            return self._receipt(
                "send_notification", "dry_run", {"channel": channel, "message": message}
            )

        return await self._post_webhook(url, payload, "send_notification")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _post_webhook(
        self, url: str, payload: Dict[str, Any], action: str
    ) -> Dict[str, Any]:
        """POST *payload* as JSON to *url*."""
        try:
            import aiohttp
        except ImportError:  # pragma: no cover
            return self._receipt(action, "error", {"reason": "aiohttp not installed"})

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
            ) as resp:
                ok = resp.status in (200, 201, 202, 204)
                return self._receipt(
                    action,
                    "sent" if ok else "error",
                    {"url": url, "http_status": resp.status},
                )

    @staticmethod
    def _receipt(action: str, status: str, detail: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "skill": "communication",
            "action": action,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **detail,
        }


__all__ = ["CommunicationSkill"]
