import discord
import DiscordCredentials
import asyncio
import requests
import json
import string
import youtube_dl
import time
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
CakeBot = Bot(command_prefix="!")

#Bot event handling

@CakeBot.event
@asyncio.coroutine
def on_voice_state_update(before, after):
	before_channel = before.voice.voice_channel
	after_channel = after.voice.voice_channel
	if after_channel != None and before_channel != after_channel:
		yield from CakeBot.send_message(after.server, after.mention + ' has joined the voice channel: ' + after_channel.name)
	elif after_channel == None:
		yield from CakeBot.send_message(before.server, before.mention + ' has left the voice channel: ' + before_channel.name)

#Bot commands

@CakeBot.command()
@asyncio.coroutine
def commands(*args):
	yield from CakeBot.say(
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
		+ "!banhammer  -- Bans a member from your server for a minute")

@CakeBot.command(pass_context=True)
@asyncio.coroutine
def banhammer(context, user: str):
	server = CakeBot.get_server(DiscordCredentials.serverID)
	channel = CakeBot.get_channel(DiscordCredentials.channelID)
	if channel.permissions_for(context.message.author).ban_members == False:
		yield from CakeBot.say("You do not have permission to ban " + user + ". Please contact your administrator for details.")
		return
	member = server.get_member_named(user)   
	if member == None:
		yield from CakeBot.say("No member named " + user) 
		return
	try:
		yield from CakeBot.ban(member, 0)
		asyncio.sleep(60)
		yield from CakeBot.unban(server, member)
	except Exception:
		yield from CakeBot.say("I do not have permission to ban users")

#League of Legends related commands

@CakeBot.command()
@asyncio.coroutine
def toptenbans(*args):
	data = requests.get('http://api.champion.gg/stats/champs/mostBanned?api_key=' + DiscordCredentials.championgg_token + '&page=1&limit=10')
	parsedData = json.loads(data.text)
	if "error" in parsedData:
		yield from CakeBot.say("Database Error!")
	else:
		topBans = ""
		for i in range(0,10):
			topBans += '---\n'
			topBans += str(i + 1) + ') ' + parsedData['data'][i]['name'] + '/' + parsedData['data'][i]['role'] 
			topBans += ' / Ban Rate: ' + str(parsedData['data'][i]['general']['banRate'])
			topBans += ' / Win Rate: ' + str(parsedData['data'][i]['general']['winPercent']) + '\n'
		yield from CakeBot.say('The top ten bans are:\n' + topBans)


@CakeBot.command()
@asyncio.coroutine
def champbuild(champion):
	champion = string.capwords(champion)
	data = requests.get('http://api.champion.gg/champion/' + champion + '/items/finished/mostWins?api_key=' + DiscordCredentials.championgg_token)
	parsedData = json.loads(data.text)
	if "error" in parsedData:
		yield from CakeBot.say("Champion does not exist!")
	else:
		yield from CakeBot.say("Most winning build for: " + champion)
		itemSet = ""
		for i in range(0,6):
			itemData = requests.get('https://global.api.pvp.net/api/lol/static-data/na/v1.2/item/' + str(parsedData[0]['items'][i]) + 
				'?api_key=' + DiscordCredentials.riot_token)
			parsedItem = json.loads(itemData.text)
			itemSet += parsedItem['name'] + "\n" + parsedItem['plaintext'] + "\n---\n"
		yield from CakeBot.say(itemSet + "\n" + str(parsedData[0]['winPercent']) + " Win Percentage")

@CakeBot.command()
@asyncio.coroutine
def champstart(champion):
	data = requests.get('http://api.champion.gg/champion/' + champion + '/items/starters/mostWins?api_key=' + DiscordCredentials.championgg_token)
	parsedData = json.loads(data.text)
	if "error" in parsedData:
		yield from CakeBot.say("Champion does not exist!")
	else:
		yield from CakeBot.say("Most winning build for: " + champion)
		itemSet = ""
		yield from CakeBot.say("Most winning starting items for: " + champion)
		for i in range(0, len(parsedData[0]['items'])):
			itemData = requests.get('https://global.api.pvp.net/api/lol/static-data/na/v1.2/item/' + str(parsedData[0]['items'][i]) + 
				'?api_key=' + DiscordCredentials.riot_token)
			parsedItem = json.loads(itemData.text)
			itemSet += parsedItem['name'] +  "\n---\n"
		yield from CakeBot.say(itemSet + "\n" + str(parsedData[0]['winPercent']) + " Win Percentage")

@CakeBot.command()
@asyncio.coroutine
def matchup(player, opponent):
	player = string.capwords(player)
	opponent = string.capwords(opponent)
	data = requests.get('http://api.champion.gg/champion/' + player + '/matchup/' + opponent +'?api_key=' + DiscordCredentials.championgg_token)
	parsedData = json.loads(data.text)
	if "error" in parsedData:
		yield from CakeBot.say("No matchup found!")
	else:
		yield from CakeBot.say(player + " has a KDA of " + str(parsedData[0]['statScore']) + " and a win rate of " + str(parsedData[0]['winRate']) + 
			"% versus "+ opponent) 

@CakeBot.command()
@asyncio.coroutine
def playlist(url:str):
	global playList
	playList.append(url)
	yield from CakeBot.say("Added your youtube video!")

@CakeBot.command()
@asyncio.coroutine
def play(*args):
	global voice
	global playList
	global player
	if len(playList) == 0:
		yield from CakeBot.say("No songs in playlist, use !playlist to add songs")
		return
	elif player is not None and player.is_playing:
		yield from CakeBot.say("Already playing " + player.title)
		return
	channel = CakeBot.get_channel(DiscordCredentials.channelID)
	if voice == None:
		voice = yield from CakeBot.join_voice_channel(channel)
	while len(playList) > 0:
		player = yield from voice.create_ytdl_player(playList.pop(0),use_avconv=True)
		player.start()
		yield from asyncio.sleep(player.duration)
	yield from voice.disconnect()

@CakeBot.command()
@asyncio.coroutine
def youtube(url: str):
	global voice
	global player
	if player is not None and player.is_playing:
		yield from CakeBot.say("Already playing " + player.title)
		return
	channel = CakeBot.get_channel(DiscordCredentials.channelID)
	if voice == None:
		voice = yield from CakeBot.join_voice_channel(channel)
	player = yield from voice.create_ytdl_player(url, use_avconv=True)
	player.start()
	yield from asyncio.sleep(player.duration)
	yield from voice.disconnect()

@CakeBot.command()
@asyncio.coroutine
def nowplaying(*args):
	global player
	if player is None:
		yield from CakeBot.say("Not currently playing anything, use command !playlist or !youtube to start")
		return
	yield from CakeBot.say("Currently Playing: " + player.title)

@CakeBot.command()
@asyncio.coroutine
def source(*args):
	yield from CakeBot.say("Sourcecode here: https://github.com/shJimmyw/CakeBot")

@CakeBot.command()
@asyncio.coroutine
def disconnect():
	global voice
	yield from voice.disconnect()

CakeBot.run(DiscordCredentials.token)