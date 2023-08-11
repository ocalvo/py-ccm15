"""Data model to represent state of a CCM15 device."""
from dataclasses import dataclass
from . import CCM15SlaveDevice

@dataclass
class CCM15DeviceState:
    """Data retrieved from a CCM15 device."""

    devices: dict[int, CCM15SlaveDevice]
