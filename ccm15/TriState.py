"""A three-valued state for optional control parameters."""
from __future__ import annotations

from enum import Enum


class TriState(Enum):
    """Three-valued state for an optional ctrl.xml command parameter.

    The CCM15 treats every control write as the complete desired state, and not
    every firmware accepts every optional parameter (e.g. the electric-heater
    `ht` flag). So these parameters are opt-in:

    - ``UNSET`` — leave the parameter out of the command entirely. This is the
      safe default; the wire output is byte-for-byte what it was before the
      parameter existed.
    - ``OFF`` / ``ON`` — send the parameter explicitly as ``0`` / ``1``.

    This is the *desired* value a caller wants written. It is deliberately
    distinct from the decoded current state (e.g. ``CCM15SlaveDevice.is_swing_on``):
    polling the device never changes a desired value, so a poll can never cause
    an opt-in parameter to start being sent.
    """

    UNSET = None
    OFF = 0
    ON = 1

    @classmethod
    def from_bool(cls, value: bool | None) -> "TriState":
        """Map ``None``/``True``/``False`` to ``UNSET``/``ON``/``OFF``."""
        if value is None:
            return cls.UNSET
        return cls.ON if value else cls.OFF

    @property
    def is_set(self) -> bool:
        """Whether the parameter should be written (i.e. not ``UNSET``)."""
        return self is not TriState.UNSET
