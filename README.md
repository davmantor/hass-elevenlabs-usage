# ElevenLabs Usage for Home Assistant

Tracks your [ElevenLabs](https://elevenlabs.io) API credit usage and call counts in Home Assistant.

## Sensors

| Sensor | Description |
|--------|-------------|
| Subscription Tier | Your account tier (free, creator, etc.) |
| Credits Used Today | Credits consumed since midnight UTC |
| Credits Used This Week | Credits consumed since Monday UTC |
| Credits Used This Month | Credits consumed since the 1st of the month UTC |
| API Calls Today | API calls made since midnight UTC |
| API Calls This Week | API calls made since Monday UTC |
| API Error | `0` = last update succeeded, `1` = failed |

## Installation

### HACS (recommended)

1. Add this repository as a custom HACS repository (Integration).
2. Install "ElevenLabs Usage" from HACS.
3. Restart Home Assistant.
4. Go to **Settings → Devices & Services → Add Integration** and search for "ElevenLabs Usage".

### Manual

Copy `custom_components/hass_elevenlabs_usage` to your HA `custom_components` directory and restart.

## Configuration

You will need your ElevenLabs API key, available at [elevenlabs.io/app/settings/api-keys](https://elevenlabs.io/app/settings/api-keys).

## Notes

- Usage data is queried from the ElevenLabs workspace analytics API using UTC-based day/week/month boundaries.
- The default polling interval is 5 minutes (300 seconds). You can adjust this in the integration options.
- If the API key becomes invalid, the integration will trigger a reauth flow in the HA UI.
