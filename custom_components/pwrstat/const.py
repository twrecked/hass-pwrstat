"""
This component provides support for pwrstat-api, a REST API wrapping
Cyberpower's pwrstat command.

"""

COMPONENT_DOMAIN = "pwrstat"
COMPONENT_MANUFACTURER = "twrecked"
COMPONENT_MODEL = "Cyberpower"

ATTR_UPS_NAME = "ups_name"
ATTR_UPS_URL = "ups_url"
ATTR_UPS_POLL_EVERY = "ups_poll_every"

DEFAULT_UPS_NAME = "localhost"
DEFAULT_UPS_URL = "http://localhost:5002/pwrstat"
DEFAULT_UPS_POLL_EVERY = 30
