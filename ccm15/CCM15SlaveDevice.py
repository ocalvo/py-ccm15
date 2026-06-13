"""Data model to represent state of a CCM15 device."""
from dataclasses import dataclass
from enum import Enum

from .TriState import TriState

@dataclass
class CCM15SlaveDevice:
    """Data retrieved from a CCM15 slave device."""

    def __init__(self, bytesarr: bytes) -> None:
        """Initialize the slave device."""
        # Seconds since this device's data was actually read from the
        # controller. 0.0 for a live read; > 0 when served from the last-good
        # cache during a transient dropout (set by
        # CCM15Device.get_status_async). Lets a consumer such as Home Assistant
        # expose a "data is N seconds old" attribute per entity.
        self.age: float = 0.0
        self.is_celsius = True
        buf = bytesarr[0]
        if (buf >> 0) & 1:
            self.is_celsius = False
        self.locked_cool_temperature: int = (buf >> 3) & 0x1F

        buf = bytesarr[1]
        self.locked_heat_temperature: int = (buf >> 0) & 0x1F
        self.locked_wind: int = (buf >> 5) & 7

        buf = bytesarr[2]
        self.locked_ac_mode: int = (buf >> 0) & 3
        self.error_code: int = (buf >> 2) & 0x3F

        buf = bytesarr[3]
        self.ac_mode: int = (buf >> 2) & 7
        self.fan_mode: int = (buf >> 5) & 7

        buf = (buf >> 1) & 1
        self.is_ac_mode_locked: bool = buf != 0

        buf = bytesarr[4]
        self.temperature_setpoint: int = (buf >> 3) & 0x1F
        if not self.is_celsius:
            self.temperature_setpoint += 62
            self.locked_cool_temperature += 62
            self.locked_heat_temperature += 62
        # Current swing state decoded from status (read-only view for display).
        self.is_swing_on: bool = (buf >> 1) & 1 != 0
        # Desired swing to write on the next control command. Distinct from the
        # decoded current state above: it defaults to UNSET (omit `sw` from the
        # command) and is only changed by an explicit caller, so polling never
        # causes `sw` to start being sent. See `desired_swing`.
        self._desired_swing: TriState = TriState.UNSET

        buf = bytesarr[5]
        if ((buf >> 3) & 1) == 0:
            self.locked_cool_temperature = 0
        if ((buf >> 4) & 1) == 0:
            self.locked_heat_temperature = 0
        self.fan_locked: bool = buf >> 5 & 1 != 0
        self.is_remote_locked: bool = ((buf >> 6) & 1) != 0

        buf = bytesarr[6]
        self.temperature: int = buf if buf < 128 else buf - 256

    @property
    def desired_swing(self) -> TriState:
        """Swing value to write on the next control command.

        ``UNSET`` (the default) omits the ``sw`` parameter from the command;
        ``ON``/``OFF`` send it explicitly. Setting this is how a caller opts in
        to swing control on firmware known to accept it.
        """
        return self._desired_swing

    @desired_swing.setter
    def desired_swing(self, value: TriState) -> None:
        self._desired_swing = value
