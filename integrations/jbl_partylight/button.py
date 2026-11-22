"""Allow an immediate BLE refresh even while the light is unavailable."""

import asyncio

from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError

from . import DOMAIN


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Expose the reconnect button alongside the lighting controls."""
    if discovery_info is not None:
        async_add_entities([ReconnectBluetooth(hass.data[DOMAIN])])


class ReconnectBluetooth(ButtonEntity):
    _attr_name = "JBL PartyLight Reconectar Bluetooth"
    _attr_icon = "mdi:bluetooth-connect"

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_unique_id = f"{coordinator.device.address}_bluetooth_reconnect"
        self._lock = asyncio.Lock()

    async def async_press(self):
        """Refresh the shared light and speed state without sending lighting commands."""
        async with self._lock:
            await self.coordinator.async_refresh()
            if not self.coordinator.last_update_success:
                raise HomeAssistantError(
                    "A JBL não respondeu. Ligue a luminária e feche o app JBL antes de tentar de novo."
                )
