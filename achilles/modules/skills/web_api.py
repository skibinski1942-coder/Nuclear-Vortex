"""
Web API Skill
=============

A generic, authenticated HTTP/REST client skill that enables the agent to
interact with any external API without writing custom integration code.

Actions:
- **get**       – HTTP GET request
- **post**      – HTTP POST with JSON or form body
- **put**       – HTTP PUT request
- **patch**     – HTTP PATCH request
- **delete**    – HTTP DELETE request
- **graphql**   – Execute a GraphQL query/mutation
- **paginate**  – Automatically page through a paginated REST endpoint

Authentication modes supported via ``api_config``::

    {
        "auth_mode":   "bearer" | "basic" | "api_key" | "oauth2" | "none",
        "token":       "...",          # bearer / oauth2
        "username":    "...",          # basic
        "password":    "...",          # basic
        "api_key":     "...",          # api_key
        "api_key_header": "X-API-Key", # header name for api_key (default shown)
        "api_key_param":  "key",       # query-param name (alternative)
        "default_headers": {"...": "..."}, # always-included headers
        "timeout":     30,             # request timeout in seconds
        "base_url":    "https://api.example.com"   # prepended when path is relative
    }
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Union
from urllib.parse import urljoin

from achilles.modules.skills import Skill

logger = logging.getLogger(__name__)


class WebAPISkill(Skill):
    """Generic authenticated HTTP/REST/GraphQL client."""

    name: str = "web_api"
    description: str = (
        "Make authenticated HTTP requests to any REST or GraphQL API. "
        "Supports bearer, basic, API-key, and OAuth2 auth modes."
    )

    def _build_action_map(self) -> Dict[str, Callable]:
        return {
            "get": self._get,
            "post": self._post,
            "put": self._put,
            "patch": self._patch,
            "delete": self._delete,
            "graphql": self._graphql,
            "paginate": self._paginate,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_url(self, url: str) -> str:
        """Prepend base_url if url is a relative path."""
        base = self.api_config.get("base_url", "")
        if base and not url.startswith(("http://", "https://")):
            return urljoin(base.rstrip("/") + "/", url.lstrip("/"))
        return url

    def _build_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Construct request headers including authentication."""
        headers: Dict[str, str] = {}
        # Default headers from config
        headers.update(self.api_config.get("default_headers", {}))

        auth_mode = self.api_config.get("auth_mode", "none")
        if auth_mode == "bearer":
            token = self.api_config.get("token", "")
            headers["Authorization"] = f"Bearer {token}"
        elif auth_mode == "api_key":
            key_header = self.api_config.get("api_key_header", "X-API-Key")
            headers[key_header] = self.api_config.get("api_key", "")
        elif auth_mode == "basic":
            import base64
            credentials = (
                f"{self.api_config.get('username', '')}:"
                f"{self.api_config.get('password', '')}"
            )
            encoded = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        # oauth2 and none: no auth header added here

        if extra:
            headers.update(extra)
        return headers

    def _build_params(self, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Append api_key as query param if configured."""
        p: Dict[str, Any] = dict(params or {})
        if self.api_config.get("auth_mode") == "api_key" and self.api_config.get("api_key_param"):
            p[self.api_config["api_key_param"]] = self.api_config.get("api_key", "")
        return p

    @staticmethod
    def _receipt(action: str, status: int, data: Any, url: str) -> Dict[str, Any]:
        return {
            "skill": "web_api",
            "action": action,
            "url": url,
            "http_status": status,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
        form_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Dispatch an HTTP request and return a normalised receipt."""
        try:
            import aiohttp
        except ImportError:
            return self._receipt(method, 0, {"error": "aiohttp not installed"}, url)

        full_url = self._resolve_url(url)
        req_headers = self._build_headers(headers)
        req_params = self._build_params(params)
        timeout = aiohttp.ClientTimeout(total=self.api_config.get("timeout", 30))

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.request(
                method.upper(),
                full_url,
                headers=req_headers,
                params=req_params or None,
                json=json_body,
                data=form_data,
            ) as resp:
                content_type = resp.headers.get("Content-Type", "")
                if "json" in content_type:
                    data = await resp.json(content_type=None)
                else:
                    data = await resp.text()
                return self._receipt(method.lower(), resp.status, data, full_url)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    async def _get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        HTTP GET request.

        Args:
            url:     Target URL (relative or absolute).
            params:  Query string parameters.
            headers: Additional request headers.
        """
        return await self._request("GET", url, headers=headers, params=params)

    async def _post(
        self,
        url: str,
        body: Optional[Any] = None,
        form_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        HTTP POST request.

        Args:
            url:       Target URL.
            body:      JSON-serialisable request body.
            form_data: Form-encoded body (mutually exclusive with *body*).
            params:    Query string parameters.
            headers:   Additional request headers.
        """
        return await self._request(
            "POST", url, headers=headers, params=params,
            json_body=body, form_data=form_data,
        )

    async def _put(
        self,
        url: str,
        body: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """HTTP PUT request."""
        return await self._request(
            "PUT", url, headers=headers, params=params, json_body=body
        )

    async def _patch(
        self,
        url: str,
        body: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """HTTP PATCH request."""
        return await self._request(
            "PATCH", url, headers=headers, params=params, json_body=body
        )

    async def _delete(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        confirmed: bool = False,
    ) -> Dict[str, Any]:
        """
        HTTP DELETE request.

        Args:
            url:       Target URL.
            params:    Query string parameters.
            headers:   Additional request headers.
            confirmed: Must be ``True`` to prevent accidental deletions.
        """
        if not confirmed:
            return {
                "skill": "web_api",
                "action": "delete",
                "status": "requires_confirmation",
                "message": "Set confirmed=True to send the DELETE request.",
                "url": url,
            }
        return await self._request("DELETE", url, headers=headers, params=params)

    async def _graphql(
        self,
        url: str,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query or mutation.

        Args:
            url:       GraphQL endpoint URL.
            query:     GraphQL query/mutation string.
            variables: Optional variables dict.
            headers:   Additional request headers.
        """
        body = {"query": query, "variables": variables or {}}
        extra_headers = {"Content-Type": "application/json"}
        if headers:
            extra_headers.update(headers)
        result = await self._request("POST", url, headers=extra_headers, json_body=body)
        return result

    async def _paginate(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        page_param: str = "page",
        page_size_param: str = "per_page",
        page_size: int = 100,
        max_pages: int = 10,
        data_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Automatically paginate through a REST endpoint.

        Args:
            url:             Target URL.
            params:          Base query parameters.
            headers:         Additional headers.
            page_param:      Query param name for the page number.
            page_size_param: Query param name for the page size.
            page_size:       Number of items per page.
            max_pages:       Maximum pages to fetch (safety limit).
            data_key:        Key in the response JSON that holds the items list.
                             If None, the entire response body is treated as the list.

        Returns:
            Dict with ``items`` (combined list), ``pages_fetched``, and ``total_items``.
        """
        base_params = dict(params or {})
        base_params[page_size_param] = page_size
        all_items: List[Any] = []

        for page in range(1, max_pages + 1):
            base_params[page_param] = page
            result = await self._request(
                "GET", url, headers=headers, params=base_params
            )
            data = result.get("data")
            items = data.get(data_key, data) if isinstance(data, dict) and data_key else data
            if not isinstance(items, list):
                break
            all_items.extend(items)
            if len(items) < page_size:
                break  # last page

        return {
            "skill": "web_api",
            "action": "paginate",
            "url": self._resolve_url(url),
            "items": all_items,
            "total_items": len(all_items),
            "pages_fetched": min(page, max_pages),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


__all__ = ["WebAPISkill"]
