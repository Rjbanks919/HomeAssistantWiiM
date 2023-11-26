"""The WiiM integration."""

from homeassistant.components.wiim.pywiim import CannotConnectError, Wiim

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DATA_INFO, DATA_WIIM

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WiiM from a config entry."""

    print("In the __init__\n")
    wiim = Wiim(entry.data[CONF_HOST], async_get_clientsession(hass))

    try:
        info = await wiim.get_device_information()
    except CannotConnectError as error:
        raise ConfigEntryNotReady from error

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_WIIM: wiim,
        DATA_INFO: info,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    print("Finished __init__\n")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
