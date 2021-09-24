import discord
from discord.ext import commands
import os
import random
import json
from configparser import ConfigParser

bot=commands.Bot(command_prefix=commands.when_mentioned_or("!v ")
                ,case_insensative=True
#                ,owner_id=338707493188272129
                ,intents=discord.Intents().all())
bot.remove_command("help")
###########################################################################
@bot.event #Loads all cogs and initiates bot
async def on_ready():
    
    with open("UWVerificationHelp.json","r") as cogFile:
        data=json.load(cogFile)
    data=data["Cogs"]
    cogList=list(data.keys())
    
    for cog in cogList: 
        cog=("Cogs."+cog)
        try: #Loads each cog
            bot.load_extension(cog)
            print ("Loaded",cog)
        except Exception as e: #If cog can't be loaded, will error to console
            print ("Error loading",cog,"e:",e)

    randNum=random.randint(1,2) #Bot status
    if randNum==1:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Badgers play games"))
    else:
        await bot.change_presence(activity=discord.Game("games with Badgers"))

    print (bot.user.name,"successfully connected to Discord")
###########################################################################
@bot.event #If user just types '!verify'
async def on_message(message):
    if message.author==bot.user: #So bot doesn't respond to itself
        return
    
    if message.content=="!":
        await message.channel.send(embed=discord.Embed(title=f"Hello {message.author}! Use `!v help` to learn more about me!"))

    await bot.process_commands(message) #Enables commands
###########################################################################
try: #Config var in Heroku
    bot.run(os.environ["DISCORDTOKEN"]) 
except: #Runs from system
    config_object=ConfigParser() 
    config_object.read("BotVariables.ini")
    variables=config_object["variables"]
    DISCORD_TOKEN=variables["DISCORD_TOKEN"]
    bot.run(DISCORD_TOKEN)