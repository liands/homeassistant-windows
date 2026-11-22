"""JBL PartyLight direct Bluetooth connection on Windows."""

import voluptuous as vol

from homeassistant.const import Platform
from homeassistant.helpers import config_validation as cv, discovery

from .coordinator import PartyLightCoordinator
from .protocol import PartyLight

DOMAIN = "jbl_partylight"
CONF_ADDRESS = "address"
CONF_SERIAL = "serial"
CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({
        vol.Required(CONF_ADDRESS): vol.All(
            cv.string, vol.Match(r"(?i)^(?:[0-9a-f]{2}:){5}[0-9a-f]{2}$")
        ),
        vol.Optional(CONF_SERIAL): vol.All(cv.string, str.strip, vol.Length(min=1)),
    })},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Load entities that share one Bluetooth connection at a time."""
    settings = config[DOMAIN]
    device = PartyLight(settings[CONF_ADDRESS].upper(), settings.get(CONF_SERIAL))
    coordinator = PartyLightCoordinator(hass, device)
    await coordinator.async_register_shutdown()
    await coordinator.async_refresh()
    hass.data[DOMAIN] = coordinator
    for platform in (Platform.LIGHT, Platform.NUMBER, Platform.BUTTON):
        hass.async_create_task(
            discovery.async_load_platform(hass, platform, DOMAIN, {}, config)
        )
    return True
