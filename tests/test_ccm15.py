import unittest
from unittest.mock import patch, MagicMock
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


if __name__ == "__main__":
    unittest.main()
