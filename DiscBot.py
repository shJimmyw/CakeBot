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
	before_channel = before.voice.voice_channel
	after_channel = after.voice.voice_channel
	if after_channel != None and before_channel != after_channel:
		yield from MacAndCheese.send_message(after.server, after.mention + " has joined the voice channel: " + after_channel.name)
	elif after_channel == None:
		yield from MacAndCheese.send_message(before.server, before.mention + " has left the voice channel: " + before_channel.name)

@MacAndCheese.event
@asyncio.coroutine
def on_member_join(member):
	yield from MacAndCheese.send_message(member.server, "Welcome " + member.mention + " to " + member.server)

#Bot commands

@MacAndCheese.command()
@asyncio.coroutine
def commands(*args):
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
		+ "!disconnect -- Disconnects this bot from the voice channel\n"
		+ "!banhammer  -- Bans a member from your server for a minute"
		+ "!dice       -- Rolls a dice between 1 and 6 or a given int greater than 1")

@MacAndCheese.command()
@asyncio.coroutine
def dice(range: int=None):
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
	if url == None:
		yield from MacAndCheese.say("I need the url of a youtube video")
		return
	global playList
	playList.append(url)
	yield from MacAndCheese.say("Added your youtube video!")

@MacAndCheese.command()
@asyncio.coroutine
def play(*args):
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
	global player
	if player is None:
		yield from MacAndCheese.say("Not currently playing anything, use command !playlist or !youtube to start")
		return
	yield from MacAndCheese.say("Currently Playing: " + player.title)

@MacAndCheese.command()
@asyncio.coroutine
def disconnect():
	global voice
	if player.is_playing():
		player.stop()
	yield from voice.disconnect()

@MacAndCheese.command()
@asyncio.coroutine
def source(*args):
	yield from MacAndCheese.say("Sourcecode here: https://github.com/shJimmyw/MacAndCheese")


MacAndCheese.run(DiscordCredentials.token)