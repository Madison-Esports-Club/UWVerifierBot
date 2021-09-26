import discord
from discord import guild
from discord.ext import commands
import os
import random
import json
from configparser import ConfigParser

from Cogs.db import dbconnect
from Cogs.verification import is_verified

bot=commands.Bot(command_prefix = commands.when_mentioned_or("!")
                ,case_insensative = True
                        ,owner_id = (139813446618185728, 338707493188272129) #DMLooter#4251, PureCache#0001
                ,intents = discord.Intents().all())
bot.remove_command("help") #Removes discord built-in help command
###########################################################################
@bot.event #Loads all cogs and initiates bot
async def on_ready():
    with open("UWVerificationHelp.json","r") as cogFile:
        data = json.load(cogFile)
    data = data["Cogs"]
    cogList = list(data.keys())

    for cog in cogList:
        cog = ("Cogs." + cog)
        try: #Loads each cog
            bot.load_extension(cog)
            print ("Loaded", cog)
        except Exception as e: #If cog can't be loaded, will error to console
            print ("Error loading", cog, "e:", e)

    randNum= random.randint(1, 2) #Bot status
    if randNum==1:
        await bot.change_presence(activity = discord.Activity(type = discord.ActivityType.watching, name = "Madison Gaming & Esports"))
    else:
        await bot.change_presence(activity = discord.Game("video games with Badgers"))

    print (bot.user.name, "successfully connected to Discord")
###########################################################################
@bot.event #Gives Verified role to user if they are in the db already
async def on_member_join(member):
    if is_verified(member.id):
        # This should be replaced with searching for a role with the name "Verified" rather than a role id, so we can use it on the child servers
        role = discord.utils.get(member.guild.roles, id = 887379146857144461) #Currently a test role, replace id with correct Verified role when added to main server
        await member.add_roles(role)
###########################################################################
@bot.event #If user just types '!'
async def on_message(message):
    if message.author == bot.user: #Ensures bot doesn't respond to itself
        return

    if message.content == "!":
        await message.channel.send(embed = discord.Embed(title = f"Hello {message.author}! Use `!v help` to learn more about me!"))

    await bot.process_commands(message) #Enables commands
###########################################################################
try: #Config var in Heroku
    bot.run(os.environ["DISCORD_TOKEN"])
except: #Runs from system
    config_object = ConfigParser()
    config_object.read("BotVariables.ini")
    variables = config_object["variables"]
    DISCORD_TOKEN = variables["DISCORD_TOKEN"]
    bot.run(DISCORD_TOKEN)
