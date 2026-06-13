"""Tests for the HTTP helpers on CCM15Device.

These cover async_send_state and async_test_connection (both httpx),
including their failure branches, which previously carried `# pragma: no
cover` and were never exercised.
"""
import unittest
from unittest.mock import patch, MagicMock

import httpx

from ccm15 import CCM15Device


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

    @patch("httpx.AsyncClient.get")
    async def test_returns_true_on_200(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        self.assertTrue(await self.ccm.async_test_connection())

    @patch("httpx.AsyncClient.get")
    async def test_returns_false_on_non_200(self, mock_get):
        mock_get.return_value = MagicMock(status_code=500)
        self.assertFalse(await self.ccm.async_test_connection())

    @patch("httpx.AsyncClient.get")
    async def test_returns_false_on_request_error(self, mock_get):
        mock_get.side_effect = httpx.ConnectError("boom")
        self.assertFalse(await self.ccm.async_test_connection())


if __name__ == "__main__":
    unittest.main()
