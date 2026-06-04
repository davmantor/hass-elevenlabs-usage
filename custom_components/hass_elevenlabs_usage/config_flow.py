"""Config flow for ElevenLabs Usage integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import aiohttp_client

from .const import (
    CONF_API_KEY,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    USER_API_URL,
)

_LOGGER = logging.getLogger(__name__)


class ElevenLabsUsageConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ElevenLabs Usage."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            tier, error = await self._validate_api_key(api_key)
            if error:
                errors[CONF_API_KEY] = error
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"ElevenLabs Usage ({tier})" if tier else "ElevenLabs Usage",
                    data={
                        CONF_API_KEY: api_key,
                    },
                    options={
                        CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Handle reauth when the API key is invalid."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauth confirmation with a new API key."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            tier, error = await self._validate_api_key(api_key)
            if error:
                errors[CONF_API_KEY] = error
            else:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates={
                        CONF_API_KEY: api_key,
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )

    async def _validate_api_key(self, api_key: str) -> tuple[str | None, str | None]:
        """Validate the API key. Returns (tier, error_key)."""
        try:
            session = aiohttp_client.async_get_clientsession(self.hass)
            resp = await session.get(
                USER_API_URL,
                headers={"xi-api-key": api_key},
                timeout=aiohttp.ClientTimeout(total=15),
            )
            if resp.status == 401:
                return None, "invalid_api_key"
            if not resp.ok:
                return None, "cannot_connect"
            data = await resp.json()
            tier = data.get("subscription", {}).get("tier")
            return tier, None
        except aiohttp.ClientError:
            _LOGGER.exception("Error validating ElevenLabs API key")
            return None, "cannot_connect"

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow."""
        return ElevenLabsUsageOptionsFlow()


class ElevenLabsUsageOptionsFlow(OptionsFlow):
    """Handle options for ElevenLabs Usage."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_UPDATE_INTERVAL, default=current_interval): vol.All(
                        int, vol.Range(min=60, max=3600)
                    ),
                }
            ),
        )
