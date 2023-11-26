"""
WiiM Platform.

WiiM API: https://www.wiimhome.com/pdf/HTTP%20API%20for%20WiiM%20Mini.pdf
"""

from math import ceil
import json
from typing import Any

from homeassistant.components.media_player import (
    BrowseMedia,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
    RepeatMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import Throttle

from .const import DOMAIN, DATA_INFO, DATA_WIIM


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the WiiM media player platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    wiim = data[DATA_WIIM]
    info = data[DATA_INFO]
    uid = config_entry.data[CONF_ID]
    name = config_entry.data[CONF_NAME]

    entity = Wiim(wiim, uid, name, info)
    async_add_entities([entity])


class Wiim(MediaPlayerEntity):
    """WiiM Player Object."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_media_content_type = MediaType.MUSIC
    _attr_supported_features = (
        MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.SEEK
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.PLAY
        # | MediaPlayerEntityFeature.PLAY_MEDIA
        # | MediaPlayerEntityFeature.VOLUME_STEP
        # | MediaPlayerEntityFeature.SELECT_SOURCE
        # | MediaPlayerEntityFeature.REPEAT_SET
        | MediaPlayerEntityFeature.SHUFFLE_SET
        # | MediaPlayerEntityFeature.CLEAR_PLAYLIST
        # | MediaPlayerEntityFeature.BROWSE_MEDIA
    )
    _attr_source_list = []

    def __init__(self, wiim, uid, name, info):
        """Initialize the media player."""
        self._wiim = wiim
        unique_id = uid
        self._playback_status = {}
        # self.thumbnail_cache = {}
        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            manufacturer="WiiM",
            model=info["hardware"],
            name=name,
            sw_version=info["firmware"],
        )

    async def async_update(self) -> None:
        """Update state."""
        print("Doing async update\n")
        self._playback_status = await self._wiim.get_playback_status()

        # TODO: Support playlists?
        # await self._async_update_playlists()

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the device."""
        status = self._playback_status.get("status", None)
        if status == "stop":
            return MediaPlayerState.PAUSED
        if status == "play":
            return MediaPlayerState.PLAYING

        return MediaPlayerState.IDLE

    @property
    def media_title(self):
        """Title of current playing media."""
        result = self._playback_status.get("Title", None)
        return bytes.fromhex(result).decode("utf-8")

    @property
    def media_artist(self):
        """Artist of current playing media (Music track only)."""
        result = self._playback_status.get("Artist", None)
        return bytes.fromhex(result).decode("utf-8")

    @property
    def media_album_name(self):
        """Album name of current playing media."""
        result = self._playback_status.get("Album", None)
        return bytes.fromhex(result).decode("utf-8")

    # TODO: Support album art via MusicBrainz API
    # URL: https://musicbrainz.org/doc/Cover_Art_Archive/API
    # @property
    # def media_image_url(self):
    #     """Image url of current playing media."""
    #     url = self._playback_status.get("albumart", Nonel
    #     return self._wiim.canonic_url(url)

    @property
    def media_seek_position(self):
        """Time in seconds of current seek position."""
        return ceil(int(self._playback_status.get("curpos", None)) / 1000)

    @property
    def media_duration(self):
        """Time in seconds of current song duration."""
        return ceil(int(self._playback_status.get("totlen", None)) / 1000)

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return self._playback_status.get("vol", None)

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        print(self._playback_status)
        return bool(int(self._playback_status.get("mute", None)))

    @property
    def shuffle(self):
        """Boolean if shuffle is enabled, this is 3 for some reason."""
        return self._playback_status.get("loop", False) == "3"

    @property
    def repeat(self) -> RepeatMode:
        """Return current repeat mode, pardon the weird values."""
        result = self._playback_status.get("loop", False)
        if result == "4":
            return RepeatMode.ALL
        elif result == "1":
            return RepeatMode.ONE
        else:
            return RepeatMode.OFF

    async def async_media_next_track(self) -> None:
        """Send media_next command to media player."""
        await self._wiim.next()

    async def async_media_previous_track(self) -> None:
        """Send media_previous command to media player."""
        await self._wiim.previous()

    async def async_media_play(self) -> None:
        """Send media_play command to media player."""
        await self._wiim.play()

    async def async_media_pause(self) -> None:
        """Send media_pause command to media player."""
        await self._wiim.pause()

    async def async_media_stop(self) -> None:
        """Send media_stop command to media player."""
        await self._wiim.stop()

    async def async_set_volume_level(self, volume: float) -> None:
        """Send volume_up command to media player."""
        await self._wiim.set_volume(int(volume * 100))

    # TODO:
    # Use the playback status to determine relative increase/decrease
    # async def async_volume_up(self) -> None:
    #     """Service to send the Volumio the command for volume up."""
    #     await self._wiim.volume_up()

    # async def async_volume_down(self) -> None:
    #     """Service to send the Volumio the command for volume down."""
    #     await self._wiim.volume_down()

    async def async_mute_volume(self, mute: bool) -> None:
        """Send mute command to media player."""
        if mute:
            await self._wiim.mute()
        else:
            await self._wiim.unmute()

    async def async_set_shuffle(self, shuffle: bool) -> None:
        """Enable/disable shuffle mode."""
        await self._wiim.set_shuffle(shuffle)

    # TODO: Implement repeat setting...
    # async def async_set_repeat(self, repeat: RepeatMode) -> None:
    #     """Set repeat mode."""
    #     if repeat == RepeatMode.OFF:
    #         await self._wiim.repeatAll("false")
    #     else:
    #         await self._wiim.repeatAll("true")

    # TODO: Evaluate these commands
    # async def async_select_source(self, source: str) -> None:
    #     """Choose an available playlist and play it."""
    #     await self._wiim.play_playlist(source)
    #     self._attr_source = source

    # async def async_clear_playlist(self) -> None:
    #     """Clear players playlist."""
    #     await self._wiim.clear_playlist()
    #     self._attr_source = None

    # @Throttle(PLAYLIST_UPDATE_INTERVAL)
    # async def _async_update_playlists(self, **kwargs):
    #     """Update available Volumio playlists."""
    #     self._attr_source_list = await self._wiim.get_playlists()

    # async def async_play_media(
    #     self, media_type: MediaType | str, media_id: str, **kwargs: Any
    # ) -> None:
    #     """Send the play_media command to the media player."""
    #     await self._wiim.replace_and_play(json.loads(media_id))

    # async def async_browse_media(
    #     self,
    #     media_content_type: MediaType | str | None = None,
    #     media_content_id: str | None = None,
    # ) -> BrowseMedia:
    #     """Implement the websocket media browsing helper."""
    #     self.thumbnail_cache = {}
    #     if media_content_type in (None, "library"):
    #         return await browse_top_level(self._wiim)

    #     return await browse_node(self, self._wiim, media_content_type, media_content_id)

    # async def async_get_browse_image(
    #     self,
    #     media_content_type: MediaType | str,
    #     media_content_id: str,
    #     media_image_id: str | None = None,
    # ) -> tuple[bytes | None, str | None]:
    #     """Get album art from Volumio."""
    #     cached_url = self.thumbnail_cache.get(media_content_id)
    #     image_url = self._wiim.canonic_url(cached_url)
    #     return await self._async_fetch_image(image_url)
