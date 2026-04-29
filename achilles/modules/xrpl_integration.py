"""
XRP Ledger Integration Module
==============================

Provides integration with the XRP Ledger (XRPL) network via:
- WebSocket: wss://s.devnet.rippletest.net:51233/
- JSON-RPC:  https://s.devnet.rippletest.net:51234/

Supports account queries, ledger data retrieval, transaction
submission, and real-time WebSocket subscriptions.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default devnet endpoints
# ---------------------------------------------------------------------------

XRPL_DEVNET_WS = "wss://s.devnet.rippletest.net:51233/"
XRPL_DEVNET_RPC = "https://s.devnet.rippletest.net:51234/"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


class XRPLNetwork(Enum):
    """Supported XRPL network environments."""

    DEVNET = "devnet"
    TESTNET = "testnet"
    MAINNET = "mainnet"


@dataclass
class XRPLConfig:
    """Configuration for the XRP Ledger integration module."""

    network: XRPLNetwork = XRPLNetwork.DEVNET
    websocket_url: str = XRPL_DEVNET_WS
    rpc_url: str = XRPL_DEVNET_RPC
    request_timeout: float = 30.0
    max_reconnect_attempts: int = 5
    reconnect_delay: float = 2.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "network": self.network.value,
            "websocket_url": self.websocket_url,
            "rpc_url": self.rpc_url,
            "request_timeout": self.request_timeout,
            "max_reconnect_attempts": self.max_reconnect_attempts,
            "reconnect_delay": self.reconnect_delay,
        }


@dataclass
class XRPLResponse:
    """Represents a response from the XRP Ledger."""

    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "error_code": self.error_code,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class XRPLSubscription:
    """Represents an active WebSocket subscription."""

    id: str
    streams: List[str]
    accounts: List[str]
    callback: Optional[Callable[[Dict[str, Any]], None]]
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "streams": self.streams,
            "accounts": self.accounts,
            "created_at": self.created_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Main integration class
# ---------------------------------------------------------------------------


class XRPLIntegration:
    """
    XRP Ledger Integration for Achilles.

    Provides two transport layers:
    - JSON-RPC over HTTPS for synchronous, request/response queries.
    - WebSocket for streaming subscriptions and lower-latency commands.

    Usage example::

        config = XRPLConfig()
        async with XRPLIntegration(config) as xrpl:
            info = await xrpl.get_server_info()
            acct = await xrpl.get_account_info("rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh")

    Or manage the connection lifecycle manually::

        xrpl = XRPLIntegration()
        await xrpl.connect_websocket()
        ...
        await xrpl.disconnect_websocket()
    """

    def __init__(self, config: Optional[XRPLConfig] = None) -> None:
        """
        Initialise the XRP Ledger Integration module.

        Args:
            config: Optional :class:`XRPLConfig`. Devnet defaults are used
                when not provided.
        """
        self.config = config or XRPLConfig()

        # aiohttp sessions – created lazily
        self._http_session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._ws_listener_task: Optional[asyncio.Task[None]] = None

        # Pending WebSocket requests keyed by request id
        self._pending: Dict[str, "asyncio.Future[Dict[str, Any]]"] = {}

        # Active subscriptions
        self._subscriptions: Dict[str, XRPLSubscription] = {}

        # Statistics
        self.stats: Dict[str, int] = {
            "rpc_requests": 0,
            "ws_commands": 0,
            "ws_reconnects": 0,
            "errors": 0,
        }

        logger.info(
            "XRPLIntegration initialised — network=%s ws=%s rpc=%s",
            self.config.network.value,
            self.config.websocket_url,
            self.config.rpc_url,
        )

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "XRPLIntegration":
        await self.connect_websocket()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.disconnect_websocket()
        await self._close_http_session()

    # ------------------------------------------------------------------
    # HTTP session management
    # ------------------------------------------------------------------

    async def _get_http_session(self) -> aiohttp.ClientSession:
        """Return (or create) the shared aiohttp session."""
        if self._http_session is None or self._http_session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
            self._http_session = aiohttp.ClientSession(timeout=timeout)
        return self._http_session

    async def _close_http_session(self) -> None:
        """Close the shared aiohttp session if open."""
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()
            self._http_session = None

    # ------------------------------------------------------------------
    # JSON-RPC transport
    # ------------------------------------------------------------------

    async def rpc_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> XRPLResponse:
        """
        Send a JSON-RPC request to the XRP Ledger HTTP endpoint.

        Args:
            method: The XRPL API method name (e.g. ``"account_info"``).
            params: Method parameters.

        Returns:
            :class:`XRPLResponse` with the parsed result.
        """
        request_id = str(uuid.uuid4())
        payload: Dict[str, Any] = {
            "method": method,
            "params": [params or {}],
        }

        logger.debug("RPC %s id=%s params=%s", method, request_id, params)

        try:
            session = await self._get_http_session()
            async with session.post(
                self.config.rpc_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as resp:
                resp.raise_for_status()
                data: Dict[str, Any] = await resp.json()

            self.stats["rpc_requests"] += 1
            return self._parse_response(data, request_id)

        except aiohttp.ClientResponseError as exc:
            self.stats["errors"] += 1
            logger.error("RPC HTTP error %s: %s", method, exc)
            return XRPLResponse(
                success=False,
                error=str(exc),
                error_code="http_error",
                request_id=request_id,
            )
        except Exception as exc:
            self.stats["errors"] += 1
            logger.error("RPC request failed %s: %s", method, exc)
            return XRPLResponse(
                success=False,
                error=str(exc),
                error_code="request_failed",
                request_id=request_id,
            )

    # ------------------------------------------------------------------
    # WebSocket transport
    # ------------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        """``True`` when the WebSocket connection is open."""
        return self._ws is not None and not self._ws.closed

    async def connect_websocket(self) -> bool:
        """
        Open a WebSocket connection to the XRP Ledger.

        Returns:
            ``True`` on success, ``False`` otherwise.
        """
        if self.is_connected:
            logger.debug("WebSocket already connected")
            return True

        attempt = 0
        while attempt < self.config.max_reconnect_attempts:
            try:
                session = await self._get_http_session()
                self._ws = await session.ws_connect(
                    self.config.websocket_url,
                    heartbeat=30.0,
                )
                # Start background listener
                self._ws_listener_task = asyncio.create_task(
                    self._ws_listener(), name="xrpl_ws_listener"
                )
                logger.info("WebSocket connected to %s", self.config.websocket_url)
                return True

            except Exception as exc:
                attempt += 1
                self.stats["ws_reconnects"] += 1
                logger.warning(
                    "WebSocket connect attempt %d/%d failed: %s",
                    attempt,
                    self.config.max_reconnect_attempts,
                    exc,
                )
                if attempt < self.config.max_reconnect_attempts:
                    await asyncio.sleep(self.config.reconnect_delay)

        self.stats["errors"] += 1
        logger.error(
            "Failed to connect to WebSocket after %d attempts",
            self.config.max_reconnect_attempts,
        )
        return False

    async def disconnect_websocket(self) -> None:
        """Close the WebSocket connection and cancel the listener task."""
        if self._ws_listener_task and not self._ws_listener_task.done():
            self._ws_listener_task.cancel()
            try:
                await self._ws_listener_task
            except asyncio.CancelledError:
                pass
            self._ws_listener_task = None

        if self._ws and not self._ws.closed:
            await self._ws.close()
        self._ws = None

        # Reject any pending futures
        for fut in self._pending.values():
            if not fut.done():
                fut.set_exception(ConnectionError("WebSocket disconnected"))
        self._pending.clear()

        logger.info("WebSocket disconnected")

    async def _ws_listener(self) -> None:
        """Background task that reads incoming WebSocket messages."""
        assert self._ws is not None
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    self._handle_ws_message(msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error("WebSocket error: %s", self._ws.exception())
                    break
                elif msg.type in (
                    aiohttp.WSMsgType.CLOSE,
                    aiohttp.WSMsgType.CLOSING,
                    aiohttp.WSMsgType.CLOSED,
                ):
                    break
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.error("WebSocket listener error: %s", exc)
        finally:
            # Reject any still-pending futures
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_exception(ConnectionError("WebSocket listener stopped"))
            self._pending.clear()

    def _handle_ws_message(self, raw: str) -> None:
        """Dispatch an incoming WebSocket message to the correct handler."""
        try:
            data: Dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning("Received non-JSON WebSocket message: %s", exc)
            return

        msg_type = data.get("type")
        request_id = data.get("id")

        if request_id and request_id in self._pending:
            fut = self._pending.pop(request_id)
            if not fut.done():
                fut.set_result(data)
            return

        # Subscription / stream messages
        if msg_type in ("ledgerClosed", "transaction", "validationReceived", "peerStatusChange"):
            self._dispatch_subscription(data)
        else:
            logger.debug("Unhandled WS message type=%s id=%s", msg_type, request_id)

    def _dispatch_subscription(self, data: Dict[str, Any]) -> None:
        """Invoke subscription callbacks for a stream message."""
        for sub in self._subscriptions.values():
            if sub.callback:
                try:
                    sub.callback(data)
                except Exception as exc:
                    logger.error("Subscription callback error: %s", exc)

    async def send_command(
        self,
        command: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> XRPLResponse:
        """
        Send a command over the WebSocket connection and await the response.

        Falls back to JSON-RPC if the WebSocket is not connected.

        Args:
            command: The XRPL command name (e.g. ``"server_info"``).
            params: Optional command parameters.

        Returns:
            :class:`XRPLResponse` with the parsed result.
        """
        if not self.is_connected:
            logger.debug("WebSocket not connected; falling back to RPC for %s", command)
            return await self.rpc_request(command, params)

        request_id = str(uuid.uuid4())
        payload: Dict[str, Any] = {"command": command, "id": request_id}
        if params:
            payload.update(params)

        loop = asyncio.get_event_loop()
        fut: "asyncio.Future[Dict[str, Any]]" = loop.create_future()
        self._pending[request_id] = fut

        try:
            assert self._ws is not None
            await self._ws.send_str(json.dumps(payload))
            self.stats["ws_commands"] += 1
            raw = await asyncio.wait_for(fut, timeout=self.config.request_timeout)
            return self._parse_response(raw, request_id)

        except asyncio.TimeoutError:
            self._pending.pop(request_id, None)
            self.stats["errors"] += 1
            return XRPLResponse(
                success=False,
                error="Request timed out",
                error_code="timeout",
                request_id=request_id,
            )
        except Exception as exc:
            self._pending.pop(request_id, None)
            self.stats["errors"] += 1
            logger.error("WebSocket command failed %s: %s", command, exc)
            return XRPLResponse(
                success=False,
                error=str(exc),
                error_code="ws_error",
                request_id=request_id,
            )

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_response(
        data: Dict[str, Any],
        request_id: Optional[str] = None,
    ) -> XRPLResponse:
        """
        Convert a raw XRPL response dict into an :class:`XRPLResponse`.

        Handles both WebSocket (``status`` / ``result`` keys) and JSON-RPC
        (``result.status`` key) response shapes.
        """
        # JSON-RPC envelope: {"result": {...}}
        if "result" in data and isinstance(data["result"], dict):
            result = data["result"]
            status = result.get("status", "")
            if status == "error" or result.get("error"):
                return XRPLResponse(
                    success=False,
                    result=result,
                    error=result.get("error_message") or result.get("error"),
                    error_code=result.get("error"),
                    request_id=request_id,
                )
            return XRPLResponse(success=True, result=result, request_id=request_id)

        # WebSocket envelope: {"status": "success"|"error", "result": {...}}
        status = data.get("status", "")
        if status == "error" or data.get("error"):
            return XRPLResponse(
                success=False,
                result=data.get("result"),
                error=data.get("error_message") or data.get("error"),
                error_code=data.get("error"),
                request_id=request_id,
            )

        return XRPLResponse(
            success=status == "success" or "result" in data,
            result=data.get("result", data),
            request_id=request_id,
        )

    # ------------------------------------------------------------------
    # Public XRPL API helpers
    # ------------------------------------------------------------------

    async def get_server_info(self) -> XRPLResponse:
        """
        Retrieve server information from the XRP Ledger node.

        Returns:
            :class:`XRPLResponse` containing build version, network id,
            ledger state, and validated ledger details.
        """
        return await self.send_command("server_info")

    async def get_ledger(
        self,
        ledger_index: str = "validated",
        transactions: bool = False,
        expand: bool = False,
    ) -> XRPLResponse:
        """
        Retrieve ledger header (and optionally transaction list).

        Args:
            ledger_index: Ledger index or shortcut (``"current"``,
                ``"closed"``, ``"validated"``).
            transactions: Include the list of transaction hashes.
            expand: Expand transaction hashes into full transaction objects.

        Returns:
            :class:`XRPLResponse` with ledger data.
        """
        return await self.send_command(
            "ledger",
            {
                "ledger_index": ledger_index,
                "transactions": transactions,
                "expand": expand,
            },
        )

    async def get_account_info(
        self,
        account: str,
        ledger_index: str = "validated",
        strict: bool = True,
    ) -> XRPLResponse:
        """
        Retrieve information about an XRP Ledger account.

        Args:
            account: The XRPL account address (``r…``).
            ledger_index: Ledger to query against.
            strict: If ``True`` only accept the classic address format.

        Returns:
            :class:`XRPLResponse` with ``AccountRoot`` ledger object.
        """
        return await self.send_command(
            "account_info",
            {
                "account": account,
                "ledger_index": ledger_index,
                "strict": strict,
            },
        )

    async def get_account_transactions(
        self,
        account: str,
        ledger_index_min: int = -1,
        ledger_index_max: int = -1,
        limit: int = 20,
        forward: bool = False,
    ) -> XRPLResponse:
        """
        Retrieve transaction history for an account.

        Args:
            account: The XRPL account address.
            ledger_index_min: Earliest ledger to include (``-1`` = earliest
                available).
            ledger_index_max: Latest ledger to include (``-1`` = latest
                available).
            limit: Maximum number of transactions to return.
            forward: If ``True``, return oldest-first order.

        Returns:
            :class:`XRPLResponse` with a list of transaction objects.
        """
        return await self.send_command(
            "account_tx",
            {
                "account": account,
                "ledger_index_min": ledger_index_min,
                "ledger_index_max": ledger_index_max,
                "limit": limit,
                "forward": forward,
            },
        )

    async def get_transaction(self, tx_hash: str) -> XRPLResponse:
        """
        Retrieve a transaction by its hash.

        Args:
            tx_hash: The SHA-256 hash of the transaction (hex string).

        Returns:
            :class:`XRPLResponse` with the transaction and its metadata.
        """
        return await self.send_command("tx", {"transaction": tx_hash, "binary": False})

    async def submit_transaction(self, tx_blob: str) -> XRPLResponse:
        """
        Submit a signed transaction to the XRP Ledger.

        The transaction must already be signed and serialised to the
        canonical binary format (hex-encoded blob).

        Args:
            tx_blob: Hex-encoded signed transaction blob.

        Returns:
            :class:`XRPLResponse` with preliminary result code and hash.
        """
        return await self.send_command("submit", {"tx_blob": tx_blob})

    async def get_account_offers(
        self,
        account: str,
        ledger_index: str = "validated",
        limit: int = 200,
    ) -> XRPLResponse:
        """
        Retrieve open currency-exchange offers for an account.

        Args:
            account: The XRPL account address.
            ledger_index: Ledger to query against.
            limit: Maximum number of offers to return.

        Returns:
            :class:`XRPLResponse` with a list of offer objects.
        """
        return await self.send_command(
            "account_offers",
            {
                "account": account,
                "ledger_index": ledger_index,
                "limit": limit,
            },
        )

    async def get_fee(self) -> XRPLResponse:
        """
        Retrieve current transaction cost (fee) information.

        Returns:
            :class:`XRPLResponse` with base fee, median fee, and open
            ledger fee in drops of XRP.
        """
        return await self.send_command("fee")

    # ------------------------------------------------------------------
    # WebSocket subscriptions
    # ------------------------------------------------------------------

    async def subscribe(
        self,
        streams: Optional[List[str]] = None,
        accounts: Optional[List[str]] = None,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Optional[XRPLSubscription]:
        """
        Subscribe to one or more XRP Ledger streams.

        Common streams: ``"ledger"``, ``"transactions"``,
        ``"transactions_proposed"``, ``"validations"``.

        Args:
            streams: List of named streams to subscribe to.
            accounts: List of account addresses to monitor for transactions.
            callback: Callable invoked with each incoming stream message.

        Returns:
            :class:`XRPLSubscription` on success, ``None`` on failure.
        """
        if not self.is_connected:
            connected = await self.connect_websocket()
            if not connected:
                return None

        params: Dict[str, Any] = {}
        if streams:
            params["streams"] = streams
        if accounts:
            params["accounts"] = accounts

        response = await self.send_command("subscribe", params)
        if not response.success:
            logger.error("Subscribe failed: %s", response.error)
            return None

        sub = XRPLSubscription(
            id=str(uuid.uuid4()),
            streams=streams or [],
            accounts=accounts or [],
            callback=callback,
        )
        self._subscriptions[sub.id] = sub
        logger.info(
            "Subscribed streams=%s accounts=%s sub_id=%s",
            streams,
            accounts,
            sub.id,
        )
        return sub

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Cancel an active subscription.

        Args:
            subscription_id: The :attr:`XRPLSubscription.id` to cancel.

        Returns:
            ``True`` if the subscription was found and cancelled.
        """
        sub = self._subscriptions.pop(subscription_id, None)
        if sub is None:
            return False

        params: Dict[str, Any] = {}
        if sub.streams:
            params["streams"] = sub.streams
        if sub.accounts:
            params["accounts"] = sub.accounts

        await self.send_command("unsubscribe", params)
        logger.info("Unsubscribed sub_id=%s", subscription_id)
        return True

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        """
        Return current module status and statistics.

        Returns:
            Dict with connection state, subscriptions, and request counts.
        """
        return {
            "network": self.config.network.value,
            "websocket_url": self.config.websocket_url,
            "rpc_url": self.config.rpc_url,
            "ws_connected": self.is_connected,
            "active_subscriptions": len(self._subscriptions),
            "subscriptions": [s.to_dict() for s in self._subscriptions.values()],
            "stats": self.stats.copy(),
        }
