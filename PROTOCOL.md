# CCM15 Protocol

This document describes the HTTP/wire protocol the Midea **CCM15** data converter
exposes, as decoded by this library (`ccm15/CCM15SlaveDevice.py`,
`ccm15/CCM15Device.py`). It is a reverse-engineering reference — Midea publishes
no protocol specification for these endpoints.

> **Note on confidence.** Field meanings below come from three sources: the
> original [houselabs/home-assistant-mideaccm](https://github.com/houselabs/home-assistant-mideaccm)
> integration (the status byte decode), the controller's own `midea.js` (the
> JavaScript the device's web UI ships — the authoritative source for the
> `sw`/`ht` command parameters and the swing/heater status bits), and
> cross-checking against [daxingplay/home-assistant-midea-ccm15](https://github.com/daxingplay/home-assistant-midea-ccm15).
> Bits marked *unverified* have only been observed on a limited number of
> controllers. See **Credits**.

## Transport

The CCM15 bridges Midea's RS-485 VRF bus to TCP/IP and serves a small HTTP
interface. Two endpoints matter:

| Method | URL | Purpose |
|--------|-----|---------|
| `GET` | `http://<host>:<port>/status.xml` | Read the state of every AC slave |
| `GET` | `http://<host>:<port>/ctrl.xml?<params>` | Write target state to one or more slaves |

The default port is `80`.

---

## `status.xml` — reading state

The response is an XML document whose children are per-slot elements named
`a0`, `a1`, … `aN` (one per addressable slave, up to 64). Each element's text is
either:

- `-` — the slot is **empty** (no AC bound to that address), or
- a comma-terminated **hex string** encoding that slave's status, e.g.
  `00000001020304,`.

Slots are **not guaranteed to be contiguous or to start at `a0`**: a controller
may report empty slots before and between populated ones (e.g. `a0`–`a3` empty,
`a4`–`a21` populated). Consumers must key off the true slot index parsed from
the element name, not a sequential counter.

```xml
<response>
  <a0>00000001020304,</a0>
  <a1>-</a1>
  <a2>00000005060708,</a2>
</response>
```

### Per-slave status bytes

Each populated slave decodes from **7 bytes** (`bytesarr[0]`–`bytesarr[6]`).
Bit 0 is the least-significant bit. Bits not listed are unused / not yet
understood.

#### Byte 0 — units & cool-limit lock

| Bits | Field | Meaning |
|------|-------|---------|
| 0 | `is_celsius` | `0` = Celsius, `1` = Fahrenheit. When Fahrenheit, the **setpoint** (byte 4) and the two **lock setpoints** (`locked_cool_temperature`, `locked_heat_temperature`) have `+62` applied. The **current temperature** (byte 6) does **not** — see the note under byte 6. |
| 3–7 | `locked_cool_temperature` | Cooling lower-limit lock setpoint. Cleared to `0` unless byte 5 bit 3 marks the lock active. |

#### Byte 1 — heat-limit lock & wind lock

| Bits | Field | Meaning |
|------|-------|---------|
| 0–4 | `locked_heat_temperature` | Heating upper-limit lock setpoint. Cleared to `0` unless byte 5 bit 4 marks the lock active. |
| 5–7 | `locked_wind` | Locked fan-speed value (when the fan is locked, see byte 5 bit 5). |

#### Byte 2 — mode lock & error

| Bits | Field | Meaning |
|------|-------|---------|
| 0–1 | `locked_ac_mode` | Raw locked-mode value (`1`→cool-lock, `2`→heat-lock, else none). |
| 2–7 | `error_code` | Fault code reported by the unit; `0` = no error. |

#### Byte 3 — current mode & fan

| Bits | Field | Meaning |
|------|-------|---------|
| 1 | `is_ac_mode_locked` | The mode is locked (cannot be changed from the unit). |
| 2–4 | `ac_mode` | Current HVAC mode — see **Mode codes**. |
| 5–7 | `fan_mode` | Current fan speed — see **Fan codes**. |

#### Byte 4 — setpoint, swing, electric heater

| Bits | Field | Meaning |
|------|-------|---------|
| 0 | `is_heater_on` | Electric auxiliary heater on/off. *(Source: `midea.js`, captured by Alexa — see Credits.)* |
| 1 | `is_swing_on` | Swing louver on/off. *(Source: `midea.js`, captured by Alexa.)* |
| 3–7 | `temperature_setpoint` | Target temperature, a 5-bit code (0–31). `+62` when Fahrenheit. The `+62` is a **display offset, not a real °C→°F conversion** (e.g. raw `16` means 16 °C in Celsius mode or 78 in Fahrenheit mode — two different physical temperatures for the same code). The unit bit (byte 0) decides which interpretation applies. |

#### Byte 5 — lock-active flags & remote lock

| Bits | Field | Meaning |
|------|-------|---------|
| 3 | (cool-lock active) | When `0`, `locked_cool_temperature` is forced to `0`. |
| 4 | (heat-lock active) | When `0`, `locked_heat_temperature` is forced to `0`. |
| 5 | `fan_locked` | Fan speed is locked. |
| 6 | `is_remote_locked` | The hand/remote controller is locked out. |

#### Byte 6 — current temperature

| Bits | Field | Meaning |
|------|-------|---------|
| 0–7 | `temperature` | Current room temperature, **signed** 8-bit (`value` if `< 128`, else `value − 256`). |

> **Fahrenheit and the current temperature.** Byte 6 is decoded **as-is — no
> `+62` offset is applied in Fahrenheit mode**, and that is correct: the
> controller emits the current temperature directly in the **active display
> unit**, so a Fahrenheit-configured device already reports the Fahrenheit value
> (e.g. `72`) in byte 6. This was confirmed on a real unit: switching the
> hand/remote controller to Fahrenheit changes byte 6 to report Fahrenheit. The
> `+62` offset applies only to the 5-bit setpoint *code* (and the lock
> setpoints), which need it to land in the Fahrenheit display range; byte 6 is
> already a full degree value, so it needs none. (The original
> [houselabs](https://github.com/houselabs/home-assistant-mideaccm) decode and
> [daxingplay](https://github.com/daxingplay/home-assistant-midea-ccm15) both
> leave `temp` raw, matching this.)

---

## `ctrl.xml` — writing state

State is written with a `GET` to `ctrl.xml` carrying query parameters. **The
controller treats every `ctrl.xml` write as the complete desired state**: any
field that is *not* sent is reset to the firmware's default (which, for mode,
lands on COOL). A single write must therefore always carry the mode, fan and
temperature it wants to keep — see the regression behavior in issue #15.

```
http://<host>:<port>/ctrl.xml?[pwd=<pwd>&]ac0=<mask>&ac1=<mask>&mode=<m>&fan=<f>&temp=<t>[&sw=<0|1>][&ht=<0|1>]
```

| Param | Required | Meaning |
|-------|----------|---------|
| `ac0` | yes | Bitmask of target slaves **0–31**: bit *i* set targets slave *i* (`2**i`). |
| `ac1` | yes | Bitmask of target slaves **32–63**: bit *(i−32)* set targets slave *i* (`2**(i−32)`). |
| `mode` | yes | Target HVAC mode — see **Mode codes**. |
| `fan` | yes | Target fan speed — see **Fan codes**. |
| `temp` | yes | Target temperature setpoint. |
| `pwd` | optional | 6-digit device password. Some firmwares reject control writes unless it is supplied; omitted otherwise. |
| `sw` | optional | Swing: `1` on, `0` off. **Opt-in** (see below). |
| `ht` | optional | Electric auxiliary heater: `1` on, `0` off. **Opt-in** (see below). |

The 64 slaves are addressed by a mask split across two 32-bit parameters
(`ac0` for 0–31, `ac1` for 32–63), matching the controller's own
`cmd_aclist()`. Writing the whole mask into `ac0` overflows for slave indices
≥ 32 and targets the wrong unit (or nothing).

### Opt-in `sw` / `ht`

`sw` and `ht` are **opt-in**: this library omits them unless a caller explicitly
sets a desired value. The reasons:

- Not every CCM15 firmware accepts these parameters. The reference
  implementations send **neither**; the controller's own web UI sends both.
- Electric auxiliary heat is *optional hardware*, not a universal feature.
- Because every write is the complete desired state, an unconditionally-sent
  parameter would be re-asserted on every command and could reset or break a
  controller that does not support it.

So the decoded *current* state (`is_swing_on`, `is_heater_on`) is kept separate
from the *desired* value a caller wants to write (`desired_swing`,
`desired_heater`, of type `TriState` — `UNSET` / `OFF` / `ON`). `UNSET` (the
default) leaves the parameter out entirely, so a poll never causes it to start
being sent.

### Mode codes (`mode=` / `ac_mode`)

| Code | Mode |
|------|------|
| 0 | Cool |
| 1 | Heat |
| 2 | Dry |
| 3 | Fan only |
| 4 | Off |
| 5 | Auto |

### Fan codes (`fan=` / `fan_mode`)

| Code | Fan speed |
|------|-----------|
| 0 | Auto |
| 2 | Low |
| 3 | Middle |
| 4 | High |
| 5 | Off |

*(Code `1` is unknown — not observed or documented; it is not mapped by any
known implementation, so its meaning has not been confirmed.)*

---

## Credits

- **Alexa ([@Alexa-RR](https://github.com/Alexa-RR))** — captured `midea.js`
  from a live CCM15 controller and traced the protocol to document the
  swing (`sw`, status byte 4 bit 1) and **electric-heater** (`ht`, status byte 4
  bit 0) parameters, including the control-URL semantics. The heater bit and the
  `sw`/`ht` command documentation here are her work.
- **[houselabs/home-assistant-mideaccm](https://github.com/houselabs/home-assistant-mideaccm)**
  (originally authored by Chao Shen) — the original reverse-engineering of the
  `status.xml` byte layout and the HVAC/fan mode mappings.
- **[daxingplay/home-assistant-midea-ccm15](https://github.com/daxingplay/home-assistant-midea-ccm15)**
  — an independent CCM15 implementation used to cross-check the decode.
