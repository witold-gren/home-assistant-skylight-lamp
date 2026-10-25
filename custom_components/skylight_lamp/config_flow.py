"""Config flow: the user enters the lamp's IP address."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import format_mac
import voluptuous as vol

from .api import SkylightClient, SkylightError
from .const import DOMAIN

STEP_USER_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})


class SkylightConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a lamp by host; the MAC address is the unique id."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            client = SkylightClient(async_get_clientsession(self.hass), host)
            try:
                info = await client.async_get_info()
            except SkylightError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(format_mac(info.mac))
                # the lamp gets its address from DHCP - follow it when re-added
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                return self.async_create_entry(
                    title=info.name or info.model or host, data={CONF_HOST: host}
                )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(STEP_USER_SCHEMA, user_input),
            errors=errors,
        )
