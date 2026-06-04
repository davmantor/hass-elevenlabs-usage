"""Constants for ElevenLabs Usage integration."""

DOMAIN = "hass_elevenlabs_usage"

# API
SUBSCRIPTION_API_URL = "https://api.elevenlabs.io/v1/user/subscription"
ANALYTICS_API_URL = (
    "https://api.elevenlabs.io/v1/workspace/analytics/query/usage-by-product-over-time"
)

# Defaults
DEFAULT_UPDATE_INTERVAL = 300  # seconds

# Config keys
CONF_API_KEY = "api_key"
CONF_UPDATE_INTERVAL = "update_interval"
# Sensor definitions: (key, name, unit, icon, device_class)
SENSOR_DEFINITIONS = [
    ("subscription_tier", "Subscription Tier", None, "mdi:account-star", None),
    ("credits_used_today", "Credits Used Today", "credits", "mdi:lightning-bolt", None),
    ("credits_used_week", "Credits Used This Week", "credits", "mdi:calendar-week", None),
    ("credits_used_month", "Credits Used This Month", "credits", "mdi:calendar-month", None),
    ("calls_today", "API Calls Today", "calls", "mdi:api", None),
    ("calls_week", "API Calls This Week", "calls", "mdi:calendar-week", None),
    ("api_error", "API Error", "errors", "mdi:alert-circle", None),
]
