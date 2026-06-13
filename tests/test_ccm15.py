import unittest
from unittest.mock import patch, MagicMock

import httpx

from ccm15 import CCM15Device, CCM15DeviceState, CCM15SlaveDevice


class TestCCM15(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.ccm = CCM15Device("localhost", 8000)

    @patch("httpx.AsyncClient.get")
    async def test_get_status_async(self, mock_get) -> None:
        """Contiguous active slots starting at 0."""
        mock_response = MagicMock()
        mock_response.text = """
        <response>
            <a0>00000001020304,</a0>
            <a1>00000005060708,</a1>
        </response>
        """
        mock_get.return_value = mock_response

        state = await self.ccm.get_status_async()
        self.assertIsInstance(state, CCM15DeviceState)
        self.assertEqual(set(state.devices.keys()), {0, 1})
        self.assertIsInstance(state.devices[0], CCM15SlaveDevice)
        self.assertIsInstance(state.devices[1], CCM15SlaveDevice)

    @patch("httpx.AsyncClient.get")
    async def test_get_status_async_noncontiguous(self, mock_get) -> None:
        """Empty slots before and between active slots must not truncate parsing."""
        mock_response = MagicMock()
        mock_response.text = """
        <response>
            <a0>-</a0>
            <a1>-</a1>
            <a2>00000001020304,</a2>
            <a3>-</a3>
            <a4>00000005060708,</a4>
        </response>
        """
        mock_get.return_value = mock_response

        state = await self.ccm.get_status_async()
        self.assertEqual(set(state.devices.keys()), {2, 4})

    @patch("httpx.AsyncClient.get")
    async def test_get_status_async_skips_malformed_entries(self, mock_get) -> None:
        """A non-slot key or a non-hex payload is skipped, not fatal."""
        mock_response = MagicMock()
        mock_response.text = """
        <response>
            <a0>00000001020304,</a0>
            <a1>nothexdata</a1>
            <bogus>00000005060708,</bogus>
        </response>
        """
        mock_get.return_value = mock_response

        state = await self.ccm.get_status_async()
        self.assertEqual(set(state.devices.keys()), {0})

    @patch("httpx.AsyncClient.get")
    async def test_empty_response_serves_cached_state(self, mock_get) -> None:
        """A transient all-'-' body returns the last good state, not empty."""
        good = MagicMock()
        good.text = "<response><a0>00000001020304,</a0></response>"
        empty = MagicMock()
        empty.text = "<response><a0>-</a0></response>"
        mock_get.side_effect = [good, empty]

        first = await self.ccm.get_status_async()
        self.assertEqual(set(first.devices.keys()), {0})
        self.assertEqual(first.devices[0].age, 0.0)  # live read
        # Age the last good read deterministically: back-to-back calls can land
        # inside a single time.monotonic() tick (coarse on some platforms), so
        # don't rely on wall-clock elapsing to prove the cached read is stamped.
        self.ccm._last_good_monotonic -= 5
        second = await self.ccm.get_status_async()
        self.assertIs(second, first)  # served from cache, identical object
        self.assertGreaterEqual(second.devices[0].age, 5.0)  # stamped as stale

    @patch("httpx.AsyncClient.get")
    async def test_exception_serves_cached_state(self, mock_get) -> None:
        """A transient fetch error returns the last good state, not a raise."""
        good = MagicMock()
        good.text = "<response><a0>00000001020304,</a0></response>"
        mock_get.side_effect = [good, httpx.ConnectTimeout("boom")]

        first = await self.ccm.get_status_async()
        second = await self.ccm.get_status_async()
        self.assertIs(second, first)

    @patch("httpx.AsyncClient.get")
    async def test_cache_expires_after_ttl(self, mock_get) -> None:
        """Past the TTL the real failure surfaces (exception propagates)."""
        ccm = CCM15Device("localhost", 8000, state_ttl=300)
        good = MagicMock()
        good.text = "<response><a0>00000001020304,</a0></response>"
        mock_get.side_effect = [good, httpx.ConnectTimeout("boom")]

        await ccm.get_status_async()
        # Backdate the last good read past the TTL window.
        ccm._last_good_monotonic -= 301
        with self.assertRaises(httpx.ConnectTimeout):
            await ccm.get_status_async()

    @patch("httpx.AsyncClient.get")
    async def test_ttl_zero_disables_cache(self, mock_get) -> None:
        """state_ttl=0 opts out: empty responses return empty state."""
        ccm = CCM15Device("localhost", 8000, state_ttl=0)
        good = MagicMock()
        good.text = "<response><a0>00000001020304,</a0></response>"
        empty = MagicMock()
        empty.text = "<response><a0>-</a0></response>"
        mock_get.side_effect = [good, empty]

        await ccm.get_status_async()
        second = await ccm.get_status_async()
        self.assertEqual(second.devices, {})

    @patch("httpx.AsyncClient.get")
    async def test_async_set_state_low_slot(self, mock_get):
        """Slots 0-31 go into ac0, ac1 is 0."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        data = MagicMock(ac_mode=0, fan_mode=0, temperature_setpoint=24)
        self.assertTrue(await self.ccm.async_set_state(4, data))

        called_url = mock_get.call_args.args[0]
        self.assertIn("ac0=16", called_url)  # 2 ** 4
        self.assertIn("ac1=0", called_url)

    @patch("httpx.AsyncClient.get")
    async def test_async_set_state_high_slot(self, mock_get):
        """Slots 32-63 go into ac1, ac0 is 0."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        data = MagicMock(ac_mode=0, fan_mode=0, temperature_setpoint=24)
        self.assertTrue(await self.ccm.async_set_state(40, data))

        called_url = mock_get.call_args.args[0]
        self.assertIn("ac0=0", called_url)
        self.assertIn("ac1=256", called_url)  # 2 ** (40 - 32)

    @patch("httpx.AsyncClient.get")
    async def test_async_set_state_sends_full_state(self, mock_get):
        """Regression test for #15.

        The CCM15 treats every ctrl.xml write as the complete desired state and
        resets any omitted field to its default (which lands on COOL). So a
        single set must always carry mode, fan AND temp together, using the
        caller's current values. Here the unit is in HEAT (mode=1) with a
        non-default fan; all three must appear in the command, otherwise the
        controller would revert to COOL.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        data = MagicMock(ac_mode=1, fan_mode=2, temperature_setpoint=26)
        self.assertTrue(await self.ccm.async_set_state(0, data))

        called_url = mock_get.call_args.args[0]
        self.assertIn("mode=1", called_url)  # HEAT preserved, not reset to COOL
        self.assertIn("fan=2", called_url)
        self.assertIn("temp=26", called_url)

    @patch("httpx.AsyncClient.get")
    async def test_set_state_url_includes_password(self, mock_get):
        """When a password is configured, the ctrl.xml URL carries pwd=."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        device = CCM15Device("localhost", 8000, password="123456")
        data = MagicMock(ac_mode=0, fan_mode=4, temperature_setpoint=22)
        self.assertTrue(await device.async_set_state(1, data))

        called_url = mock_get.call_args.args[0]
        self.assertIn("pwd=123456", called_url)
        self.assertIn("ac0=2", called_url)  # 2 ** 1

    @patch("httpx.AsyncClient.get")
    async def test_set_state_url_omits_password_when_unset(self, mock_get):
        """Without a password the URL must not include a pwd parameter."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        device = CCM15Device("localhost", 8000)
        data = MagicMock(ac_mode=1, fan_mode=2, temperature_setpoint=18)
        await device.async_set_state(0, data)

        called_url = mock_get.call_args.args[0]
        self.assertNotIn("pwd=", called_url)

    async def test_uses_injected_client_when_provided(self) -> None:
        """A client passed to the constructor is reused instead of building a new one."""
        injected = MagicMock(spec=httpx.AsyncClient)
        device = CCM15Device("localhost", 8000, client=injected)
        self.assertIs(device._get_client(), injected)

    async def test_builds_client_when_not_provided(self) -> None:
        """Standalone callers can still use the library without an injected client."""
        device = CCM15Device("localhost", 8000)
        client = device._get_client()
        self.assertIsInstance(client, httpx.AsyncClient)
        # Lazy creation is cached for the lifetime of the device.
        self.assertIs(device._get_client(), client)

    async def test_aclose_closes_self_built_client(self) -> None:
        """A client the library built is closed (no leak) on aclose()."""
        device = CCM15Device("localhost", 8000)
        built = device._get_client()
        await device.aclose()
        self.assertTrue(built.is_closed)
        self.assertIsNone(device._client)
        # Idempotent: a second close is a no-op, not an error.
        await device.aclose()

    async def test_aclose_leaves_injected_client_open(self) -> None:
        """An injected client is owned by the caller and must not be closed."""
        injected = httpx.AsyncClient()
        device = CCM15Device("localhost", 8000, client=injected)
        await device.aclose()
        self.assertFalse(injected.is_closed)
        self.assertIs(device._client, injected)
        await injected.aclose()

    async def test_context_manager_closes_self_built_client(self) -> None:
        """`async with CCM15Device(...)` closes a self-built client on exit."""
        async with CCM15Device("localhost", 8000) as device:
            built = device._get_client()
            self.assertFalse(built.is_closed)
        self.assertTrue(built.is_closed)


if __name__ == "__main__":
    unittest.main()
