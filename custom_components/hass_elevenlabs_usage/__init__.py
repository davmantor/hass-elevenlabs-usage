"""ElevenLabs Usage integration for Home Assistant."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ANALYTICS_API_URL,
    CONF_API_KEY,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    SUBSCRIPTION_API_URL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

type ElevenLabsUsageConfigEntry = ConfigEntry[ElevenLabsUsageCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: ElevenLabsUsageConfigEntry) -> bool:
    """Set up ElevenLabs Usage from a config entry."""
    coordinator = ElevenLabsUsageCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ElevenLabsUsageConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(
    hass: HomeAssistant, entry: ElevenLabsUsageConfigEntry
) -> None:
    """Handle options update."""
    coordinator: ElevenLabsUsageCoordinator = entry.runtime_data
    interval = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    coordinator.update_interval = timedelta(seconds=interval)


class ElevenLabsUsageCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch ElevenLabs usage data."""

    config_entry: ElevenLabsUsageConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ElevenLabsUsageConfigEntry) -> None:
        """Initialize the coordinator."""
        interval = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
            config_entry=entry,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch usage data from ElevenLabs API."""
        api_key = self.config_entry.data[CONF_API_KEY]
        headers = {"xi-api-key": api_key}
        session = aiohttp_client.async_get_clientsession(self.hass)

        try:
            resp = await session.get(
                SUBSCRIPTION_API_URL,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            )
            if resp.status == 401:
                raise ConfigEntryAuthFailed("ElevenLabs API key is invalid or revoked")
            resp.raise_for_status()
            subscription = await resp.json()

            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=today_start.weekday())
            month_start = today_start.replace(day=1)

            today_raw = await self._fetch_analytics(session, headers, today_start, now)
            week_raw = await self._fetch_analytics(session, headers, week_start, now)
            month_raw = await self._fetch_analytics(session, headers, month_start, now)

        except ConfigEntryAuthFailed:
            raise
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error fetching ElevenLabs data: {err}") from err

        return _build_data(subscription, today_raw, week_raw, month_raw)

    async def _fetch_analytics(
        self,
        session: aiohttp.ClientSession,
        headers: dict[str, str],
        start: datetime,
        end: datetime,
    ) -> dict[str, Any]:
        """POST to analytics endpoint for a specific time window."""
        payload = {
            "start_time": int(start.timestamp() * 1000),
            "end_time": int(end.timestamp() * 1000),
            "interval_seconds": 86400,
        }
        resp = await session.post(
            ANALYTICS_API_URL,
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=15),
        )
        if resp.status == 401:
            raise ConfigEntryAuthFailed("ElevenLabs API key is invalid or revoked")
        resp.raise_for_status()
        return await resp.json()


def _build_data(
    subscription: dict[str, Any],
    today_raw: dict[str, Any],
    week_raw: dict[str, Any],
    month_raw: dict[str, Any],
) -> dict[str, Any]:
    """Build the flat sensor data dict from all API responses."""
    data: dict[str, Any] = {}
    data["subscription_tier"] = subscription.get("tier")

    today_credits, today_calls = _parse_analytics(today_raw)
    week_credits, week_calls = _parse_analytics(week_raw)
    month_credits, _ = _parse_analytics(month_raw)  # calls_month sensor not defined

    data["credits_used_today"] = today_credits
    data["calls_today"] = today_calls
    data["credits_used_week"] = week_credits
    data["calls_week"] = week_calls
    data["credits_used_month"] = month_credits

    return data


def _parse_analytics(raw: dict[str, Any]) -> tuple[float | None, int | None]:
    """Parse analytics tabular response into (credits_total, calls_total).

    Locates the credits column by column_units == 'credits'.
    Locates the call count column by a name containing 'count' or 'request'.
    Returns (None, None) if rows are empty.
    """
    columns = raw.get("columns", [])
    column_units = raw.get("column_units", [])
    rows = raw.get("rows", [])

    if not columns or not rows:
        return None, None

    credits_idx = next(
        (i for i, unit in enumerate(column_units) if unit == "credits"),
        None,
    )
    calls_idx = next(
        (
            i
            for i, col in enumerate(columns)
            if "count" in col.lower() or "request" in col.lower()
        ),
        None,
    )

    if credits_idx is None:
        _LOGGER.warning(
            "Analytics response has no 'credits' unit column — credits sensors unavailable. "
            "Columns: %s, Units: %s",
            columns,
            column_units,
        )
    if calls_idx is None:
        _LOGGER.warning(
            "Analytics response has no count/request column — call count sensors unavailable. "
            "Columns: %s",
            columns,
        )

    credits_total: float | None = None
    if credits_idx is not None:
        total = sum(
            row[credits_idx]
            for row in rows
            if credits_idx < len(row) and isinstance(row[credits_idx], (int, float))
        )
        credits_total = round(float(total), 6)

    calls_total: int | None = None
    if calls_idx is not None:
        calls_total = int(sum(
            row[calls_idx]
            for row in rows
            if calls_idx < len(row) and isinstance(row[calls_idx], (int, float))
        ))

    return credits_total, calls_total
