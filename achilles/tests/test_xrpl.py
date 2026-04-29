"""
Tests for XRP Ledger Integration Module
========================================

Tests cover configuration, response parsing, the public API helpers,
and subscription management without requiring a live network connection.
All WebSocket and HTTP calls are mocked.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from achilles.modules.xrpl_integration import (
    XRPL_DEVNET_RPC,
    XRPL_DEVNET_WS,
    XRPLConfig,
    XRPLIntegration,
    XRPLNetwork,
    XRPLResponse,
    XRPLSubscription,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ok_ws_response(command: str, request_id: str) -> Dict[str, Any]:
    """Build a minimal successful WebSocket-style XRPL response."""
    return {
        "id": request_id,
        "status": "success",
        "type": "response",
        "result": {"command": command, "status": "success"},
    }


def _err_ws_response(request_id: str, error: str = "notYetImplemented") -> Dict[str, Any]:
    return {
        "id": request_id,
        "status": "error",
        "error": error,
        "error_message": f"Error: {error}",
    }


# ---------------------------------------------------------------------------
# XRPLConfig
# ---------------------------------------------------------------------------


class TestXRPLConfig:
    def test_defaults(self) -> None:
        cfg = XRPLConfig()
        assert cfg.network == XRPLNetwork.DEVNET
        assert cfg.websocket_url == XRPL_DEVNET_WS
        assert cfg.rpc_url == XRPL_DEVNET_RPC
        assert cfg.request_timeout == 30.0

    def test_to_dict(self) -> None:
        cfg = XRPLConfig()
        d = cfg.to_dict()
        assert d["network"] == "devnet"
        assert d["websocket_url"] == XRPL_DEVNET_WS
        assert d["rpc_url"] == XRPL_DEVNET_RPC
        assert d["request_timeout"] == 30.0

    def test_custom_network(self) -> None:
        cfg = XRPLConfig(
            network=XRPLNetwork.MAINNET,
            websocket_url="wss://xrplcluster.com/",
            rpc_url="https://s1.ripple.com:51234/",
        )
        assert cfg.network == XRPLNetwork.MAINNET
        assert "xrplcluster" in cfg.websocket_url


# ---------------------------------------------------------------------------
# XRPLResponse
# ---------------------------------------------------------------------------


class TestXRPLResponse:
    def test_success_response(self) -> None:
        r = XRPLResponse(success=True, result={"foo": "bar"})
        assert r.success
        assert r.result == {"foo": "bar"}
        assert r.error is None

    def test_error_response(self) -> None:
        r = XRPLResponse(success=False, error="actNotFound", error_code="actNotFound")
        assert not r.success
        assert r.error == "actNotFound"

    def test_to_dict(self) -> None:
        r = XRPLResponse(success=True, result={"x": 1}, request_id="abc")
        d = r.to_dict()
        assert d["success"] is True
        assert d["result"] == {"x": 1}
        assert d["request_id"] == "abc"
        assert "timestamp" in d


# ---------------------------------------------------------------------------
# XRPLIntegration – initialisation & status
# ---------------------------------------------------------------------------


class TestXRPLIntegrationInit:
    def test_default_init(self) -> None:
        xrpl = XRPLIntegration()
        assert xrpl.config.network == XRPLNetwork.DEVNET
        assert not xrpl.is_connected
        assert xrpl.stats["rpc_requests"] == 0

    def test_custom_config(self) -> None:
        cfg = XRPLConfig(network=XRPLNetwork.TESTNET)
        xrpl = XRPLIntegration(cfg)
        assert xrpl.config.network == XRPLNetwork.TESTNET

    def test_get_status(self) -> None:
        xrpl = XRPLIntegration()
        status = xrpl.get_status()
        assert status["network"] == "devnet"
        assert status["ws_connected"] is False
        assert status["active_subscriptions"] == 0
        assert "stats" in status


# ---------------------------------------------------------------------------
# XRPLIntegration – _parse_response (static)
# ---------------------------------------------------------------------------


class TestParseResponse:
    def test_ws_success(self) -> None:
        data = {"status": "success", "result": {"ledger_index": 100}}
        r = XRPLIntegration._parse_response(data, "req-1")
        assert r.success
        assert r.result["ledger_index"] == 100
        assert r.request_id == "req-1"

    def test_ws_error(self) -> None:
        data = {"status": "error", "error": "actNotFound", "error_message": "Account not found"}
        r = XRPLIntegration._parse_response(data)
        assert not r.success
        assert r.error == "Account not found"
        assert r.error_code == "actNotFound"

    def test_rpc_success(self) -> None:
        data = {"result": {"status": "success", "server_state": "full"}}
        r = XRPLIntegration._parse_response(data)
        assert r.success
        assert r.result["server_state"] == "full"

    def test_rpc_error(self) -> None:
        data = {
            "result": {
                "status": "error",
                "error": "tooBusy",
                "error_message": "Server too busy",
            }
        }
        r = XRPLIntegration._parse_response(data)
        assert not r.success
        assert r.error_code == "tooBusy"


# ---------------------------------------------------------------------------
# XRPLIntegration – JSON-RPC transport
# ---------------------------------------------------------------------------


class TestRPCRequest:
    @pytest.mark.asyncio
    async def test_rpc_success(self) -> None:
        xrpl = XRPLIntegration()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = AsyncMock(
            return_value={"result": {"status": "success", "info": {}}}
        )
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.closed = False

        xrpl._http_session = mock_session  # type: ignore[assignment]

        r = await xrpl.rpc_request("server_info")
        assert r.success
        assert xrpl.stats["rpc_requests"] == 1

    @pytest.mark.asyncio
    async def test_rpc_http_error(self) -> None:
        import aiohttp

        xrpl = XRPLIntegration()
        mock_session = MagicMock()
        mock_session.closed = False

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(
            side_effect=aiohttp.ClientResponseError(
                request_info=MagicMock(), history=(), status=500
            )
        )
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        mock_session.post = MagicMock(return_value=mock_cm)
        xrpl._http_session = mock_session  # type: ignore[assignment]

        r = await xrpl.rpc_request("server_info")
        assert not r.success
        assert r.error_code == "http_error"
        assert xrpl.stats["errors"] == 1


# ---------------------------------------------------------------------------
# XRPLIntegration – WebSocket transport
# ---------------------------------------------------------------------------


class TestWebSocketTransport:
    @pytest.mark.asyncio
    async def test_connect_success(self) -> None:
        xrpl = XRPLIntegration()

        mock_ws = MagicMock()
        mock_ws.closed = False

        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.ws_connect = AsyncMock(return_value=mock_ws)
        xrpl._http_session = mock_session  # type: ignore[assignment]

        # Patch asyncio.create_task so the listener doesn't actually run
        with patch("asyncio.create_task", return_value=MagicMock()) as mock_task:
            result = await xrpl.connect_websocket()

        assert result is True
        assert xrpl._ws is mock_ws

    @pytest.mark.asyncio
    async def test_connect_failure_exhausts_retries(self) -> None:
        cfg = XRPLConfig(max_reconnect_attempts=2, reconnect_delay=0.0)
        xrpl = XRPLIntegration(cfg)

        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.ws_connect = AsyncMock(side_effect=ConnectionError("refused"))
        xrpl._http_session = mock_session  # type: ignore[assignment]

        result = await xrpl.connect_websocket()
        assert result is False
        assert xrpl.stats["errors"] == 1

    @pytest.mark.asyncio
    async def test_is_connected_false_when_ws_none(self) -> None:
        xrpl = XRPLIntegration()
        assert not xrpl.is_connected

    @pytest.mark.asyncio
    async def test_disconnect_clears_state(self) -> None:
        xrpl = XRPLIntegration()

        mock_ws = MagicMock()
        mock_ws.closed = False
        mock_ws.close = AsyncMock()
        xrpl._ws = mock_ws  # type: ignore[assignment]

        mock_task = MagicMock()
        mock_task.done = MagicMock(return_value=True)
        xrpl._ws_listener_task = mock_task  # type: ignore[assignment]

        await xrpl.disconnect_websocket()
        assert xrpl._ws is None
        mock_ws.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_command_falls_back_to_rpc(self) -> None:
        """send_command should use RPC when WebSocket is not connected."""
        xrpl = XRPLIntegration()

        # Patch rpc_request
        xrpl.rpc_request = AsyncMock(  # type: ignore[method-assign]
            return_value=XRPLResponse(success=True, result={"status": "success"})
        )

        r = await xrpl.send_command("server_info")
        assert r.success
        xrpl.rpc_request.assert_awaited_once_with("server_info", None)

    @pytest.mark.asyncio
    async def test_send_command_via_websocket(self) -> None:
        xrpl = XRPLIntegration()

        # Simulate a connected WebSocket
        mock_ws = MagicMock()
        mock_ws.closed = False

        captured_id: Dict[str, str] = {}

        async def fake_send_str(payload_str: str) -> None:
            payload = json.loads(payload_str)
            captured_id["id"] = payload["id"]
            # Resolve the pending future
            fut = xrpl._pending.get(payload["id"])
            if fut and not fut.done():
                fut.set_result(_ok_ws_response("server_info", payload["id"]))

        mock_ws.send_str = fake_send_str
        xrpl._ws = mock_ws  # type: ignore[assignment]

        r = await xrpl.send_command("server_info")
        assert r.success

    @pytest.mark.asyncio
    async def test_send_command_timeout(self) -> None:
        cfg = XRPLConfig(request_timeout=0.01)
        xrpl = XRPLIntegration(cfg)

        mock_ws = MagicMock()
        mock_ws.closed = False
        mock_ws.send_str = AsyncMock()  # never resolves the future
        xrpl._ws = mock_ws  # type: ignore[assignment]

        r = await xrpl.send_command("server_info")
        assert not r.success
        assert r.error_code == "timeout"
        assert xrpl.stats["errors"] == 1


# ---------------------------------------------------------------------------
# XRPLIntegration – public API helpers
# ---------------------------------------------------------------------------


class TestPublicAPIHelpers:
    def _make_xrpl(self) -> XRPLIntegration:
        """Return an integration instance with send_command mocked."""
        xrpl = XRPLIntegration()
        xrpl.send_command = AsyncMock(  # type: ignore[method-assign]
            return_value=XRPLResponse(success=True, result={"status": "success"})
        )
        return xrpl

    @pytest.mark.asyncio
    async def test_get_server_info(self) -> None:
        xrpl = self._make_xrpl()
        r = await xrpl.get_server_info()
        assert r.success
        xrpl.send_command.assert_awaited_once_with("server_info")

    @pytest.mark.asyncio
    async def test_get_ledger_defaults(self) -> None:
        xrpl = self._make_xrpl()
        await xrpl.get_ledger()
        xrpl.send_command.assert_awaited_once_with(
            "ledger",
            {"ledger_index": "validated", "transactions": False, "expand": False},
        )

    @pytest.mark.asyncio
    async def test_get_ledger_with_transactions(self) -> None:
        xrpl = self._make_xrpl()
        await xrpl.get_ledger(ledger_index="current", transactions=True, expand=True)
        call_params = xrpl.send_command.await_args[0][1]
        assert call_params["transactions"] is True
        assert call_params["expand"] is True

    @pytest.mark.asyncio
    async def test_get_account_info(self) -> None:
        xrpl = self._make_xrpl()
        addr = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"
        await xrpl.get_account_info(addr)
        call_params = xrpl.send_command.await_args[0][1]
        assert call_params["account"] == addr
        assert call_params["strict"] is True

    @pytest.mark.asyncio
    async def test_get_account_transactions(self) -> None:
        xrpl = self._make_xrpl()
        await xrpl.get_account_transactions("rTest123", limit=10, forward=True)
        call_params = xrpl.send_command.await_args[0][1]
        assert call_params["limit"] == 10
        assert call_params["forward"] is True

    @pytest.mark.asyncio
    async def test_get_transaction(self) -> None:
        xrpl = self._make_xrpl()
        tx_hash = "A" * 64
        await xrpl.get_transaction(tx_hash)
        call_params = xrpl.send_command.await_args[0][1]
        assert call_params["transaction"] == tx_hash
        assert call_params["binary"] is False

    @pytest.mark.asyncio
    async def test_submit_transaction(self) -> None:
        xrpl = self._make_xrpl()
        blob = "DEADBEEF" * 20
        await xrpl.submit_transaction(blob)
        call_params = xrpl.send_command.await_args[0][1]
        assert call_params["tx_blob"] == blob

    @pytest.mark.asyncio
    async def test_get_account_offers(self) -> None:
        xrpl = self._make_xrpl()
        await xrpl.get_account_offers("rTest123", limit=50)
        call_params = xrpl.send_command.await_args[0][1]
        assert call_params["limit"] == 50

    @pytest.mark.asyncio
    async def test_get_fee(self) -> None:
        xrpl = self._make_xrpl()
        r = await xrpl.get_fee()
        assert r.success
        xrpl.send_command.assert_awaited_once_with("fee")


# ---------------------------------------------------------------------------
# XRPLIntegration – subscriptions
# ---------------------------------------------------------------------------


class TestSubscriptions:
    @pytest.mark.asyncio
    async def test_subscribe_success(self) -> None:
        xrpl = XRPLIntegration()
        # Simulate connected WS
        mock_ws = MagicMock()
        mock_ws.closed = False
        xrpl._ws = mock_ws  # type: ignore[assignment]

        xrpl.send_command = AsyncMock(  # type: ignore[method-assign]
            return_value=XRPLResponse(success=True, result={})
        )

        callback_calls = []
        sub = await xrpl.subscribe(
            streams=["ledger"],
            accounts=["rTest123"],
            callback=lambda msg: callback_calls.append(msg),
        )

        assert sub is not None
        assert sub.id in xrpl._subscriptions
        assert "ledger" in sub.streams
        assert xrpl.get_status()["active_subscriptions"] == 1

    @pytest.mark.asyncio
    async def test_subscribe_failure(self) -> None:
        xrpl = XRPLIntegration()
        mock_ws = MagicMock()
        mock_ws.closed = False
        xrpl._ws = mock_ws  # type: ignore[assignment]

        xrpl.send_command = AsyncMock(  # type: ignore[method-assign]
            return_value=XRPLResponse(success=False, error="badStream")
        )

        sub = await xrpl.subscribe(streams=["unknown_stream"])
        assert sub is None
        assert xrpl.get_status()["active_subscriptions"] == 0

    @pytest.mark.asyncio
    async def test_unsubscribe(self) -> None:
        xrpl = XRPLIntegration()
        mock_ws = MagicMock()
        mock_ws.closed = False
        xrpl._ws = mock_ws  # type: ignore[assignment]

        xrpl.send_command = AsyncMock(  # type: ignore[method-assign]
            return_value=XRPLResponse(success=True, result={})
        )

        sub = await xrpl.subscribe(streams=["ledger"])
        assert sub is not None
        assert await xrpl.unsubscribe(sub.id) is True
        assert xrpl.get_status()["active_subscriptions"] == 0

    @pytest.mark.asyncio
    async def test_unsubscribe_unknown_id(self) -> None:
        xrpl = XRPLIntegration()
        assert await xrpl.unsubscribe("nonexistent-id") is False

    def test_dispatch_subscription_callback(self) -> None:
        xrpl = XRPLIntegration()
        received: list = []

        sub = XRPLSubscription(
            id="s1",
            streams=["ledger"],
            accounts=[],
            callback=lambda msg: received.append(msg),
        )
        xrpl._subscriptions["s1"] = sub

        msg = {"type": "ledgerClosed", "ledger_index": 200}
        xrpl._dispatch_subscription(msg)
        assert received == [msg]


# ---------------------------------------------------------------------------
# XRPLIntegration – context manager
# ---------------------------------------------------------------------------


class TestContextManager:
    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        xrpl = XRPLIntegration()
        xrpl.connect_websocket = AsyncMock(return_value=True)  # type: ignore[method-assign]
        xrpl.disconnect_websocket = AsyncMock()  # type: ignore[method-assign]
        xrpl._close_http_session = AsyncMock()  # type: ignore[method-assign]

        async with xrpl as ctx:
            assert ctx is xrpl

        xrpl.connect_websocket.assert_awaited_once()
        xrpl.disconnect_websocket.assert_awaited_once()
        xrpl._close_http_session.assert_awaited_once()


# ---------------------------------------------------------------------------
# XRPLIntegration – _handle_ws_message
# ---------------------------------------------------------------------------


class TestHandleWSMessage:
    def test_invalid_json_is_ignored(self) -> None:
        xrpl = XRPLIntegration()
        # Should not raise
        xrpl._handle_ws_message("not-valid-json{{{")

    def test_resolves_pending_future(self) -> None:
        xrpl = XRPLIntegration()
        loop = asyncio.new_event_loop()
        try:
            fut = loop.create_future()
            req_id = "req-42"
            xrpl._pending[req_id] = fut
            msg = json.dumps({"id": req_id, "status": "success", "result": {}})
            xrpl._handle_ws_message(msg)
            assert fut.done()
            assert fut.result()["status"] == "success"
        finally:
            loop.close()

    def test_dispatches_stream_message(self) -> None:
        xrpl = XRPLIntegration()
        received: list = []

        sub = XRPLSubscription(
            id="s1",
            streams=["ledger"],
            accounts=[],
            callback=lambda m: received.append(m),
        )
        xrpl._subscriptions["s1"] = sub

        msg = json.dumps({"type": "ledgerClosed", "ledger_index": 300})
        xrpl._handle_ws_message(msg)
        assert len(received) == 1
        assert received[0]["ledger_index"] == 300


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
