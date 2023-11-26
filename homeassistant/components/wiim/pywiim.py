"""Implementation of a WiiM interface."""
import json
import asyncio
import aiohttp


class Wiim:
    """A connection to WiiM."""

    def __init__(self, host, session=None):
        """Initialize the object."""
        self._host = host
        self._created_session = False
        self._session = session

    def _init_session(self):
        if self._session == None:
            self._session = aiohttp.ClientSession()
            self._created_session = True

    async def close(self):
        """Close the connection."""
        if self._created_session and self._session is not None:
            await self._session.close()
            self._session = None
            self._created_session = False

    async def _get_wiim_msg(self, method, params=None):
        url = f"https://{self._host}/httpapi.asp?command={method}"
        print("Using URL: " + url)
        try:
            self._init_session()
            response = await self._session.get(url, verify_ssl=False, params=params)
            if response.status == 200:
                return json.loads(await response.text())
            else:
                raise CannotConnectError(response)
        except aiohttp.client_exceptions.ContentTypeError:
            # hack to handle methods not supported by older versions
            return {}
        except (asyncio.TimeoutError, aiohttp.ClientError) as error:
            raise CannotConnectError() from error

    async def get_device_information(self):
        """Get the device information."""
        response = await self._get_wiim_msg("getStatusEx")
        print("Here's that response...\n")
        print(response.copy())
        return response.copy()

    async def get_connection_status(self):
        """Get the WiFi connection status."""
        response = await self._get_wiim_msg("wlanGetConnectState")
        return response.copy()

    async def get_playback_status(self):
        """Get the wiim state."""
        response = await self._get_wiim_msg("getPlayerStatus")
        return response.copy()

    async def pause(self):
        """Send 'pause' command to wiim."""
        await self._get_wiim_msg("setPlayerCmd:pause")

    async def play(self):
        """Send 'play' command to wiim."""
        await self._get_wiim_msg("setPlayerCmd:play")

    async def toggle(self):
        """Send 'toggle pause/play' command to wiim."""
        await self._get_wiim_msg("setPlayerCmd:onepause")

    async def previous(self):
        """Send 'previous' command to wiim."""
        await self._get_wiim_msg("setPlayerCmd:prev")

    async def next(self):
        """Send 'next' command to wiim."""
        await self._get_wiim_msg("setPlayerCmd:next")

    async def seek(self, duration):
        """Send 'seek <DURATION>' command to wiim (0 -> duration in sec)."""
        await self._get_wiim_msg(f"setPlayerCmd:seek:{duration}")

    async def stop(self):
        """Send 'stop' command to wiim."""
        await self._get_wiim_msg("setPlayerCmd:stop")

    async def set_volume(self, volume):
        """Send volume level to wiim (0 -> 100)."""
        await self._get_wiim_msg(f"setPlayerCmd:vol:{volume}")

    async def mute(self):
        """Send 'mute' command to wiim."""
        await self._get_wiim_msg("setPlayerCmd:mute:1")

    async def unmute(self):
        """Send 'unmute' command to wiim."""
        await self._get_wiim_msg("setPlayerCmd:mute:0")

    async def set_shuffle(self, shuffle):
        """Enable/disable shuffle mode."""
        shuffle_str = "2" if shuffle_str else "0"
        await self._get_wiim_msg(f"setPlayerCmd:loopmode:{shuffle_str}")


class CannotConnectError(Exception):
    """Exception to indicate an error in connection."""
