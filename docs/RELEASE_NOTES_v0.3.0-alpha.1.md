# Release Notes — v0.3.0-alpha.1

Version `0.3.0-alpha.1` is a major modernization release of **hass-pwrstat**, bringing the Home Assistant component, Python implementation, Docker container, and documentation up to the latest standards.

---

## What's New

### 1. Built-in Native Energy Sensor (`kWh`)
* Added `PwrStatEnergySensor` that automatically integrates UPS `Load` (Watts) into cumulative kilowatt-hours (`kWh`).
* Inherits from `RestoreEntity` to preserve accumulated energy across Home Assistant restarts.
* Features `device_class = SensorDeviceClass.ENERGY` and `state_class = SensorStateClass.TOTAL_INCREASING`.
* Integrates directly into the **Home Assistant Energy Dashboard** with zero manual YAML or helper configuration.

### 2. New Load Percentage Sensor
* Automatically extracts and presents UPS load as a percentage (`%`) alongside the Watt measurement for quick visual monitoring on dashboards.

### 3. Home Assistant Best Practices Modernization
* **Typed Config Entries & Runtime Data**: Migrated to `type PwrStatConfigEntry = ConfigEntry[PwrStatCoordinator]` and `entry.runtime_data = coordinator`, deprecating integration-level global state in `hass.data`.
* **Standard Entity Naming**: Implemented `_attr_has_entity_name = True` and removed manual `self.entity_id = ...` hardcoding, allowing Home Assistant's entity registry and user customization to work seamlessly while maintaining backward-compatible `unique_id`s.
* **Dynamic Device Registry**: Device info is now dynamically enriched with real hardware properties from the UPS (`Model Name`, `Firmware Number`, and `CyberPower` manufacturer).
* **Typed Numeric States**: Power (W), Voltage (V), Battery (%), and Remaining Runtime (min) sensors now return actual numeric values (`int` / `float`) instead of raw strings, enabling Home Assistant's long-term statistics and recorder graphs.
* **Connection Validation**: Config flow now validates API connectivity with a live request, providing actionable error messages (`cannot_connect`, `invalid_response`).
* **Options Flow**: Added options flow support to adjust polling intervals and API URLs directly from the UI without reinstalling the integration.
* **Strings & Translations**: Added `strings.json` as the single source of truth for UI translations.

### 4. Modernized Docker API (`extras/pwrstat/`)
* **Standard Flask**: Removed abandoned `flask-jsonpify` and unnecessary `flask_restful` dependencies; now powered by clean, modern Flask.
* **Robust Regex Output Parsing**: Implemented regex parsing for `pwrstat -status` that cleanly separates keys from values without deleting or mangling periods in firmware versions, decimals, or timestamps.
* **Container Healthcheck**: Added `/health` endpoint and configured Docker healthchecks in `docker-compose.yaml`.
* **Lightweight Base Image**: Switched from bloated `python:3` (~1 GB) to `python:3.12-slim` (~140 MB).
* **Signals & Graceful Termination**: Docker container entrypoint uses `exec` for immediate signal handling upon container stop.

### 5. HACS Custom Repository Ready
* Added root `hacs.json` for first-class recognition in HACS as a custom repository.
* Added HACS badge and clear installation instructions in `README.md`.

---

## Upgrade Instructions

### HACS
1. Open **HACS** > **Integrations** > **Custom repositories** (three dots in top right).
2. Add `https://github.com/twrecked/hass-pwrstat` with Category **Integration**.
3. Install version `0.3.0-alpha.1` and restart Home Assistant.

### Manual / Script
Run `./install go /path/to/homeassistant/config` and restart Home Assistant.
