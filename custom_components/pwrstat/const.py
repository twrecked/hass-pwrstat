"""Constants for the pwrstat (Cyberpower) integration."""

from typing import Final

DOMAIN: Final = "pwrstat"
COMPONENT_DOMAIN: Final = DOMAIN
COMPONENT_MANUFACTURER: Final = "CyberPower"
COMPONENT_MODEL: Final = "UPS"

ATTR_UPS_NAME: Final = "ups_name"
ATTR_UPS_URL: Final = "ups_url"
ATTR_UPS_POLL_EVERY: Final = "ups_poll_every"

CONF_UPS_NAME: Final = ATTR_UPS_NAME
CONF_UPS_URL: Final = ATTR_UPS_URL
CONF_UPS_POLL_EVERY: Final = ATTR_UPS_POLL_EVERY

DEFAULT_UPS_NAME: Final = "localhost"
DEFAULT_UPS_URL: Final = "http://localhost:5002/pwrstat"
DEFAULT_UPS_POLL_EVERY: Final = 30
DEFAULT_TIMEOUT: Final = 10
