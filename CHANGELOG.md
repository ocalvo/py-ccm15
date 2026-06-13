# Changelog

## [0.5.0](https://github.com/ocalvo/py-ccm15/compare/v0.4.0...v0.5.0) (2026-06-13)


### Features

* opt-in swing control via a TriState desired value ([#43](https://github.com/ocalvo/py-ccm15/issues/43)) ([c95bf12](https://github.com/ocalvo/py-ccm15/commit/c95bf127bc7fc9ef454fad50e793be8875227d49))

## [0.4.0](https://github.com/ocalvo/py-ccm15/compare/v0.3.0...v0.4.0) (2026-06-13)


### Features

* optional password (pwd=) authentication for control commands ([#17](https://github.com/ocalvo/py-ccm15/issues/17)) ([85a635f](https://github.com/ocalvo/py-ccm15/commit/85a635f3358e3b62b60ac877d91a2812b84dac82))

## [0.3.0](https://github.com/ocalvo/py-ccm15/compare/v0.2.4...v0.3.0) (2026-06-13)


### Features

* accept an injected httpx.AsyncClient and manage its lifecycle ([#40](https://github.com/ocalvo/py-ccm15/issues/40)) ([dc145c2](https://github.com/ocalvo/py-ccm15/commit/dc145c29232d7d5b80d107b2e49583c0b319632b))

## [0.2.4](https://github.com/ocalvo/py-ccm15/compare/v0.2.3...v0.2.4) (2026-06-13)


### Bug Fixes

* tolerate transient CCM15 dropouts and report per-device data age ([#34](https://github.com/ocalvo/py-ccm15/issues/34)) ([fe1529c](https://github.com/ocalvo/py-ccm15/commit/fe1529c58964823a084cdeaaf98d6b7607444d7d))

## [0.2.3](https://github.com/ocalvo/py-ccm15/compare/v0.2.2...v0.2.3) (2026-06-13)


### Documentation

* attribute CCM15 protocol to houselabs/home-assistant-mideaccm ([#30](https://github.com/ocalvo/py-ccm15/issues/30)) ([0e788ef](https://github.com/ocalvo/py-ccm15/commit/0e788efa95f53236377ab61fb64fb15c4bbf007b))
* note that this library is consumed by Home Assistant core ([#27](https://github.com/ocalvo/py-ccm15/issues/27)) ([f28101d](https://github.com/ocalvo/py-ccm15/commit/f28101db628611db860d09fb3da602ef50fcbbbf))

## [0.2.2](https://github.com/ocalvo/py-ccm15/compare/v0.2.1...v0.2.2) (2026-06-13)


### Bug Fixes

* handle non-contiguous slots and slaves &gt;= 32 ([#23](https://github.com/ocalvo/py-ccm15/issues/23)) ([d9d7e58](https://github.com/ocalvo/py-ccm15/commit/d9d7e5890d5cf3baf02adc4e28a1e5a3c2fdb80a))

## [0.2.1](https://github.com/ocalvo/py-ccm15/compare/v0.2.0...v0.2.1) (2026-06-13)


### Bug Fixes

* update async_set_state test to current API ([#21](https://github.com/ocalvo/py-ccm15/issues/21)) ([842bd33](https://github.com/ocalvo/py-ccm15/commit/842bd33bad32b53fafad85a567eb0558ce4947de))

## [0.2.0](https://github.com/ocalvo/py-ccm15/compare/v0.1.2...v0.2.0) (2026-06-13)


### Features

* add release-please for automated releases ([#19](https://github.com/ocalvo/py-ccm15/issues/19)) ([7624545](https://github.com/ocalvo/py-ccm15/commit/7624545e23d80ebe58bbe32e09e7ab09f790a874))
