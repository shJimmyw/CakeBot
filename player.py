import discord
import asyncio
import youtube_dl
import string


class vidPlayer:

    def __init__(self, bot):
        self.bot = bot
        self.list = []
        self.voice = None
        self.player = None

    @asyncio.coroutine
    def playAll(self, channel: discord.Channel=None):
        if len(self.list) == 0:
            self.bot.say("No videos in the playlist")
            return
        if self.voice is None:
            self.voice = yield from self.bot.join_voice_channel(channel)
        self.player = yield from self.voice.create_ytdl_player(self.list.pop(0), after=self.threadsafePlayNext, use_avconv=True)
        self.player.start()


    @asyncio.coroutine
    def playlist(self, url: str=None):
        self.list.append(url)
        yield from self.bot.say("Added your video!")

    @asyncio.coroutine
    def play(self, url: str=None, channel: discord.Channel=None):
        if self.voice is None:
            self.voice = yield from self.bot.join_voice_channel(channel)
        self.player = yield from self.voice.create_ytdl_player(url, after=self.threadsafeDisconnect, use_avconv=True)
        self.player.start()

    @asyncio.coroutine
    def disconnect(self):
        if self.voice is None:
            pass
        else:
            yield from self.voice.disconnect()
            self.player.stop()
            self.voice = None
            self.player = None

    def threadsafeDisconnect(self):
        coro = self.voice.disconnect()
        fut = discord.compat.run_coroutine_threadsafe(coro, self.voice.loop)
        try:
            fut.result()
            self.voice = None
            self.player.stop()
            self.player = None
        except:
            pass

    def threadsafePlayNext(self):
        self.player.stop()
        if self.list != []:
            coro = self.playAll()
            fut = discord.compat.run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except:
                pass
        else:
            coro = self.voice.disconnect()
            fut = discord.compat.run_coroutine_threadsafe(coro, self.voice.loop)
            try:
                fut.result()
                self.voice = None
                self.player = None
            except:
                pass

    @asyncio.coroutine
    def changeVolume(self, vol: int=None):
        if self.player is None:
            yield from self.bot.say("Can't change volume, no audio to adjust")
        elif vol is None:
            yield from self.bot.say("What do you want the volume at? Please include a number")
        elif vol > 200:
            self.player.volume = 2
            yield from self.bot.say("Volume is at 200")
        elif vol < 0:
            self.player.volume = 0
            yield from self.bot.say("Volume is at 0")
        else:
            self.player.volume = vol/100
            yield from self.bot.say("Volume is at " + str(vol))

    @asyncio.coroutine
    def getVolume(self):
        if self.player is None:
            yield from self.bot.say("Not currently playing anything")
        else:
            yield from self.bot.say("Volume is " + str(self.player.volume))

    @asyncio.coroutine
    def now(self):
        if self.player is None:
            yield from self.bot.say("Not currently playing anything, use command !add or !youtube to start")
        else:
            yield from self.bot.say("Currently Playing: " + self.player.title)

    @asyncio.coroutine
    def pauseAndResume(self):
        if self.player is None:
            pass
        elif self.player.is_playing():
            self.player.pause()
            yield from self.bot.say(self.player.title + " paused")
        elif self.player.is_playing() is False:
            self.player.resume()
            yield from self.bot.say(self.player.title + " resumed")

    @asyncio.coroutine
    def skip(self):
        if self.player is None:
            pass
        else:
            self.player.stop()
            self.playAll()
