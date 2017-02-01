# CakeBot
A Discord Bot written with the discord.py api wrapper developed by Rapptz that uses the Riot Games League of Legends API as well as the champion.gg API. This bot was made for fun and for personal use. There is no set update schedule. 

##Requirements

* Python 3.4.2
* Discord.py with voice support which you can find [here](https://github.com/Rapptz/discord.py)
* A Riot Games API key which you can obtain [here](https://developer.riotgames.com/)
* A champion.gg API key obtainable [here](http://api.champion.gg/)
* Either [ffmpeg](https://ffmpeg.org/download.html) or [avconv](https://libav.org/download/) 

You will also need the following python packages (These should be found on pip):
  * [youtube-dl](https://rg3.github.io/youtube-dl/) 
  * [requests](http://docs.python-requests.org/en/master/user/install/#install)
  * [PyNaCl](https://pypi.python.org/pypi/PyNaCl/)

##Setup

For setup, open the DiscordCredentials.py file and insert your server and channel id, discord bot token, and api keys in their specified locations. Then simply run the DiscBot.py file.

##Functionality

###League of Legends Related

  * Given a champion it can display the most winning final item build and most winning starting items.
  * Given two champions can display the win rate of the first champion against the second, if they are generally played against each other.
  * Displays the top 10 highest banned champions in the game, although it should be noted that the same champion can show up multiple times if it is played in 
    multiple roles

###Non-League of Legends Related

  * Functional youtube functionality that will play the audio of the given youtube url
  * Add multiple youtube videos to create an in server playlist
  * Ban users for a minute if the bot and user both have permission
  * Informs server via chat when another user joins a voice channel or leaves all voice channels in the server
  * Random number generator for fun


See !commands for a full list of commands and their respective functionality.

