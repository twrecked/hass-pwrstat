# Release Notes — v0.3.0-beta.1

Version `0.3.0-beta.1` stabilizes the 0.3.0 series, refining sensor naming and standardizing entity IDs for clean, predictable Home Assistant integrations.

---

## What's Changed

### 1. Renamed Binary Sensor to "Utility Power"
* Renamed the primary utility power state binary sensor from **Power** to **Utility Power** (`binary_sensor.<ups_id>_utility_power`).
* Provides clearer distinction in dashboards and device cards between line utility power availability and overall UPS status or load.
* Updated documentation in `README.md` to reflect the new sensor naming.

### 2. Explicit Default Entity IDs
* Explicitly sets default `entity_id` values based on unique entity IDs across all sensors:
  * Binary sensors (`binary_sensor.<ups_id>_<suffix>`)
  * Telemetry sensors (`sensor.<ups_id>_<suffix>`)
  * Energy accumulator sensors (`sensor.<ups_id>_energy`)
* Guarantees consistent, predictable entity IDs on fresh installations while preserving user customizations made via the Home Assistant UI.

### 3. Repository Organization
* Consolidated maintenance and installation tooling (`install`, `publish-release`) under the `scripts/` directory.

---

## Upgrade Instructions

### HACS
1. Open **HACS** > **Integrations** > **pwrstat (Cyberpower) Support**.
2. Select **Redownload** (or update if prompted) and choose version `0.3.0-beta.1`.
3. Restart Home Assistant.

> **Note on Entity Names:**
> If you tested `0.3.0-alpha.1`, the binary sensor formerly named `Power` is now named `Utility Power`. Home Assistant may update the entity or create the new entity `binary_sensor.<ups_id>_utility_power`. Check your dashboards or automations if you referenced the old entity ID.

### Manual / Script
Run `./scripts/install go /path/to/homeassistant/config` and restart Home Assistant.
