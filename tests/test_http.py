"""Tests for the HTTP helpers on CCM15Device.

These cover async_send_state (httpx) and async_test_connection (aiohttp),
including their failure branches, which previously carried `# pragma: no
cover` and were never exercised.
"""
import unittest
from unittest.mock import patch, MagicMock

import aiohttp
import httpx

from ccm15 import CCM15Device


class _AsyncCM:
    """Minimal async context manager yielding a fixed value."""

    def __init__(self, value):
        self._value = value

    async def __aenter__(self):
        return self._value

    async def __aexit__(self, *exc_info):
        return False


class TestAsyncSendState(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.ccm = CCM15Device("localhost", 8000)

    @patch("httpx.AsyncClient.get")
    async def test_returns_true_on_ok(self, mock_get):
        mock_get.return_value = MagicMock(status_code=httpx.codes.OK)
        self.assertTrue(await self.ccm.async_send_state("http://x/ctrl.xml"))

    @patch("httpx.AsyncClient.get")
    async def test_returns_true_on_found(self, mock_get):
        mock_get.return_value = MagicMock(status_code=httpx.codes.FOUND)
        self.assertTrue(await self.ccm.async_send_state("http://x/ctrl.xml"))

    @patch("httpx.AsyncClient.get")
    async def test_returns_false_on_error_status(self, mock_get):
        mock_get.return_value = MagicMock(status_code=httpx.codes.INTERNAL_SERVER_ERROR)
        self.assertFalse(await self.ccm.async_send_state("http://x/ctrl.xml"))


class TestAsyncTestConnection(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.ccm = CCM15Device("localhost", 8000)

    def _patch_session(self, *, status=None, get_side_effect=None):
        """Patch aiohttp.ClientSession so `async with ... as session` yields a
        mock whose .get(...) is itself an async CM yielding a response."""
        session = MagicMock()
        if get_side_effect is not None:
            session.get = MagicMock(side_effect=get_side_effect)
        else:
            response = MagicMock(status=status)
            session.get = MagicMock(return_value=_AsyncCM(response))
        return patch("aiohttp.ClientSession", return_value=_AsyncCM(session))

    async def test_returns_true_on_200(self):
        with self._patch_session(status=200):
            self.assertTrue(await self.ccm.async_test_connection())

    async def test_returns_false_on_non_200(self):
        with self._patch_session(status=500):
            self.assertFalse(await self.ccm.async_test_connection())

    async def test_returns_false_on_client_error(self):
        with self._patch_session(get_side_effect=aiohttp.ClientError()):
            self.assertFalse(await self.ccm.async_test_connection())


if __name__ == "__main__":
    unittest.main()
