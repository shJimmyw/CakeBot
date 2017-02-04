import discord
import DiscordCredentials
import asyncio
import requests
import json
import string
import youtube_dl
import time
import random
import logging
from discord.ext.commands import Bot

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

voice = None
player = None
playList = []
client = discord.Client()
MacAndCheese = Bot(command_prefix="!")

#Bot event handling

@MacAndCheese.event
@asyncio.coroutine
def on_voice_state_update(before, after):
	"""Detects when a user's voice state changes.
	If the user is in a different voice channel than before, a message is sent telling other users which channel the user has joined.
	If the user is no longer in any voice channel, a message is sent telling other users which channel the user has left

	"""

	before_channel = before.voice.voice_channel
	after_channel = after.voice.voice_channel
	if after_channel != None and before_channel != after_channel:
		yield from MacAndCheese.send_message(after.server, after.mention + " has joined the voice channel: " + after_channel.name)
	elif after_channel == None:
		yield from MacAndCheese.send_message(before.server, before.mention + " has left the voice channel: " + before_channel.name)

@MacAndCheese.event
@asyncio.coroutine
def on_member_join(member):
	"""Upon a neww user joining the server, a message is sent to the other users via the general chat that a new
	user has joined the server.

	"""

	yield from MacAndCheese.send_message(member.server, "Welcome " + member.mention + " to " + member.server)

#Bot commands

@MacAndCheese.command()
@asyncio.coroutine
def commands(*args):
	"""!commands

	This command asks the bot to display a list of commands and their expected functionality.

	"""

	yield from MacAndCheese.say(
		  "!commands   -- Displays all commands\n"
		+ "!toptenbans -- Displays current 10 most banned champions\n"
		+ "!champbuild -- Displays most winning final build for the given champion\n"
		+ "!champstart -- Displays most winning starting items for the given champion\n"
		+ "!matchup    -- Displays the win percentage and KDA for a given champion and enemy champion\n"
		+ "!playlist   -- Takes a youtube url and adds it to the bot playlist\n"
		+ "!play       -- Plays all videos currently in the playlist\n"
		+ "!youtube    -- Plays a youtube video given a youtube url\n"
		+ "!nowplaying -- Displays title of currently playing youtube video\n"
		+ "!getVolume  -- Get current volume of video"
		+ "!volume     -- Sets the volume of the player to a percentage"
		+ "!disconnect -- Disconnects this bot from the voice channel\n"
		+ "!banhammer  -- Bans a member from your server for a minute"
		+ "!dice       -- Rolls a dice between 1 and 6 or a given int greater than 1")

@MacAndCheese.command()
@asyncio.coroutine
def dice(range: int=None):
	"""!dice

	Args: 
		range (int): Upper Limit in range of numbers

	If the user provides zero arguments, the bot randomly delivers an integer between 1 and 6 inclusive.
	If the user provides one argument, N, that is greater than 1, it delivers an integer between 1 and N inclusive.
	If the user provides either 0 or 1 as an argument, it prompts the user to provide a valid integer greater than 1.

	"""

	if range == None:
		output = random.randint(1,6)
	elif range > 1:
		output = random.randint(1,range)
	else:
		yield from MacAndCheese.say("Pick an integer greater than 1")
		return
	yield from MacAndCheese.say("Rolling a dice...\nDice landed on: " + str(output))


@MacAndCheese.command(pass_context=True)
@asyncio.coroutine
def banhammer(context, user: str=None):
	"""!banhammer
	
	Args:
		user (str): Name of user intended to be banned
	
	If the user does not provide an argument, the bot prompts the user for one.
	When provided an argument the bot checks if the user has ban permissions and if not will
	ask prompt the user to contact the server administrator. If the user does have permission
	it will check to see if the argument provided is the name of a valid user, if so it will 
	then proceed to ban the given user for a minute before unbanning them.

	"""

	if user == None:
		yield from MacAndCheese.say("Who do you want me to ban?")
		return
	server = MacAndCheese.get_server(DiscordCredentials.serverID)
	channel = MacAndCheese.get_channel(DiscordCredentials.channelID)
	if channel.permissions_for(context.message.author).ban_members == False:
		yield from MacAndCheese.say("You do not have permission to ban " + user + ". Please contact your administrator for details.")
		return
	member = server.get_member_named(user)   
	if member == None:
		yield from MacAndCheese.say("No member named " + user) 
		return
	try:
		yield from MacAndCheese.ban(member, 0)
		asyncio.sleep(60)
		yield from MacAndCheese.unban(server, member)
	except Exception:
		yield from MacAndCheese.say("I do not have permission to ban users")

#League of Legends related commands

@MacAndCheese.command()
@asyncio.coroutine
def toptenbans(*args):
	"""!toptenbans

	The bot makes a GET request through the champion.gg api. It provides the top ten banned champions as recorded by the champion.gg
	database. The champions also have their ban rate and win percentage provided.

	"""

	data = requests.get('http://api.champion.gg/stats/champs/mostBanned?api_key=' + DiscordCredentials.championgg_token + '&page=1&limit=10')
	parsedData = json.loads(data.text)
	if "error" in parsedData:
		yield from MacAndCheese.say("Database Error!")
	else:
		topBans = ""
		for i in range(0,10):
			topBans += '---\n'
			topBans += str(i + 1) + ') ' + parsedData['data'][i]['name'] + '/' + parsedData['data'][i]['role'] 
			topBans += ' / Ban Rate: ' + str(parsedData['data'][i]['general']['banRate'])
			topBans += ' / Win Rate: ' + str(parsedData['data'][i]['general']['winPercent']) + '\n'
		yield from MacAndCheese.say('The top ten bans are:\n' + topBans)


@MacAndCheese.command()
@asyncio.coroutine
def champbuild(champion: str=None):
	"""!champbuild

	args:
		champion(string): The name of the champion to lookup

	The bot makes a GET request on champion.gg using the given argument as a champion name. If there's no such champion recorded in the database
	then an error is given. Otherwise it takes the returned information and looks up each item on the Riot Games API with a GET request. The bot
	then gives a list of the names of the items it looked up and the champion's winrate with the set of items.

	"""

	if champion == None:
		yield from MacAndCheese.say("What champion am I looking up?")
		return
	champion = string.capwords(champion)
	data = requests.get('http://api.champion.gg/champion/' + champion + '/items/finished/mostWins?api_key=' + DiscordCredentials.championgg_token)
	parsedData = json.loads(data.text)
	if "error" in parsedData:
		yield from MacAndCheese.say("Champion does not exist!")
	else:
		yield from MacAndCheese.say("Most winning build for: " + champion)
		itemSet = ""
		for i in range(0,6):
			itemData = requests.get('https://global.api.pvp.net/api/lol/static-data/na/v1.2/item/' + str(parsedData[0]['items'][i]) + 
				'?api_key=' + DiscordCredentials.riot_token)
			parsedItem = json.loads(itemData.text)
			itemSet += parsedItem['name'] + "\n" + parsedItem['plaintext'] + "\n---\n"
		yield from MacAndCheese.say(itemSet + "\n" + str(parsedData[0]['winPercent']) + " Win Percentage")

@MacAndCheese.command()
@asyncio.coroutine
def champstart(champion: str=None):
	"""!champstart

	args:
		champion(string): The name of the champion to lookup

	The bot makes a GET request on champion.gg using the given argument as a champion name. If there's no such champion recorded in the database
	then an error is given. Otherwise it takes the returned information and looks up each item on the Riot Games API with a GET request. The bot
	then gives a list of the names of the items it looked up and the champion's winrate with the starting items.

	"""

	if champion == None:
		yield from MacAndCheese.say("What champion am I looking up?")
		return
	data = requests.get('http://api.champion.gg/champion/' + champion + '/items/starters/mostWins?api_key=' + DiscordCredentials.championgg_token)
	parsedData = json.loads(data.text)
	if "error" in parsedData:
		yield from MacAndCheese.say("Champion does not exist!")
	else:
		yield from MacAndCheese.say("Most winning build for: " + champion)
		itemSet = ""
		yield from MacAndCheese.say("Most winning starting items for: " + champion)
		for i in range(0, len(parsedData[0]['items'])):
			itemData = requests.get('https://global.api.pvp.net/api/lol/static-data/na/v1.2/item/' + str(parsedData[0]['items'][i]) + 
				'?api_key=' + DiscordCredentials.riot_token)
			parsedItem = json.loads(itemData.text)
			itemSet += parsedItem['name'] +  "\n---\n"
		yield from MacAndCheese.say(itemSet + "\n" + str(parsedData[0]['winPercent']) + " Win Percentage")

@MacAndCheese.command()
@asyncio.coroutine
def matchup(player: str=None, opponent: str=None):
	"""!matchup

	args:
		player(string): The name of the champion the user is playing
		opponent(string): The enemy champion the user is comparing the first one with

	The bot makes a GET request on champion.gg using the given arguments as champion names. The bot then sends a message that provides the winrate
	and KDA ratio that the first champion has versus the second one. 

	"""

	if player == None or opponent == None:
		yield from MacAndCheese.say("I need the names of two champions. Try again")
		return
	player = string.capwords(player)
	opponent = string.capwords(opponent)
	data = requests.get('http://api.champion.gg/champion/' + player + '/matchup/' + opponent +'?api_key=' + DiscordCredentials.championgg_token)
	parsedData = json.loads(data.text)
	if "error" in parsedData:
		yield from MacAndCheese.say("No matchup found!")
	else:
		yield from MacAndCheese.say(player + " has a KDA of " + str(parsedData[0]['statScore']) + " and a win rate of " + str(parsedData[0]['winRate']) + 
			"% versus "+ opponent) 

#Youtube Commands start here

@MacAndCheese.command()
@asyncio.coroutine
def playlist(url: str=None):
	"""
	!playlist

	args:
		url(string): The url of the youtube video to be added to the playlist

		Takes a string as the url of a youtube video and adds it to a list of strings.

	"""

	if url == None:
		yield from MacAndCheese.say("I need the url of a youtube video")
		return
	global playList
	playList.append(url)
	yield from MacAndCheese.say("Added your youtube video!")

@MacAndCheese.command()
@asyncio.coroutine
def play(*args):
	"""
	!play

		Begins playing each video in the playlist variable. If the playlist is empty it prompts the users to add videos.
		While the playlist is not empty it enters the given voice channel and plays a video in a FIFO order and does
	    an asynchronous sleep for the video's duration and then plays the next one in the list. If during this there 
	    are no more videos in the list, it will automatically disconnect from the voice channel.

	"""	

	global voice
	global playList
	global player
	if len(playList) == 0:
		yield from MacAndCheese.say("No songs in playlist, use !playlist to add songs")
		return
	elif player is not None and player.is_playing:
		yield from MacAndCheese.say("Already playing " + player.title)
		return
	channel = MacAndCheese.get_channel(DiscordCredentials.channelID)
	if voice == None:
		voice = yield from MacAndCheese.join_voice_channel(channel)
	while len(playList) > 0:
		player = yield from voice.create_ytdl_player(playList.pop(0),use_avconv=True)
		player.start()
		yield from asyncio.sleep(player.duration)
	yield from voice.disconnect()

@MacAndCheese.command()
@asyncio.coroutine
def youtube(url: str=None):
	"""!youtube
	
	args: 
		url(string) : The url of the youtube video to be played

	The bot enters the voice channel and plays the youtube video in the url given in the argument. At the end of the video it will automatically
	disconnect from the channel.


	"""

	if url == None:
		yield from MacAndCheese.say("I need the url of a youtube video")
		return
	global voice
	global player
	if player is not None and player.is_playing:
		yield from MacAndCheese.say("Already playing " + player.title)
		return
	channel = MacAndCheese.get_channel(DiscordCredentials.channelID)
	if voice == None:
		voice = yield from MacAndCheese.join_voice_channel(channel)
	player = yield from voice.create_ytdl_player(url, use_avconv=True)
	player.start()
	yield from asyncio.sleep(player.duration)
	yield from voice.disconnect()

@MacAndCheese.command()
@asyncio.coroutine
def nowplaying(*args):
	"""!nowplaying

	The bot displays the title of the video currently playing. If there is no such video it will prompt the user to add one.

	"""

	global player
	if player is None:
		yield from MacAndCheese.say("Not currently playing anything, use command !playlist or !youtube to start")
		return
	yield from MacAndCheese.say("Currently Playing: " + player.title)

@MacAndCheese.command()
@asyncio.coroutine
def getVolume(*args):
	"""!getVolume

	The bot displays the current volume level of the video being played. 

	"""
	if player is None or player.is_playing == False:
		yield from MacAndCheese.say("Not currently playing a video!")

	yield from MacAndCheese.say("Volume level is currently at " + str(player.volume * 100))


@MacAndCheese.command()
@asyncio.coroutine
def volume(vol_level: int=None):
	"""!volume

	args: 
		vol_level(int) : The volume to set the player to

	The bot gets an integer between 0 and 200 inclusive and sets the audio player's volume to that percentage. If the argument is less than 0 or 
	greater than 200, it will instead default it to 0 or 200 respectively. If there is no currently playing video, it will inform the user of this.

	"""
	if vol_level == None:
		yield from MacAndCheese.say("What do you want the volume at? Please include a number")
	elif: player is None or player.is_playing == False:
		yield from MacAndCheese.say("Not currently playing a video!")
	elif vol_level > 200:
		player.volume = 2
		yield from MacAndCheese.say("Volume level requested is too high, defaulting to max")
	elif vol_level < 0:
		player.volume = 0
		yield from MacAndCheese.say("Volume level requested is too low, defaulting to minimum")
	else:
		player.volume = vol_level/100
		yield from MacAndCheese.say("Volume is now: " + str(vol_level))


@MacAndCheese.command()
@asyncio.coroutine
def disconnect():
	"""!disconnect

	Disconnects the bot from the current voice channel and stops playing any video currently played.

	"""
	global voice
	if player.is_playing():
		player.stop()
	yield from voice.disconnect()

@MacAndCheese.command()
@asyncio.coroutine
def source(*args):
	"""!source
		
	Provides the source code in a github link for this bot.

	"""
	yield from MacAndCheese.say("Sourcecode here: https://github.com/shJimmyw/MacAndCheese")


MacAndCheese.run(DiscordCredentials.token)