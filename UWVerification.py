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
		for role in member.guild.roles: #Checks to see if Verified role exists
			if role.name.lower()=="verified":
				verifiedRole=role
				break
		'''if not verifiedRole: #If Verified role doesn't exist, creates one			
			perms = discord.Permissions(send_messages = True)
			verifiedRole = await member.guild.create_role(name = "Verified", color = discord.Color.dark_grey(), permissions = perms)
			for channel in member.guild.channels:
				await channel.set_permissions(verifiedRole, send_messages = True)'''

		#role = discord.utils.get(member.guild.roles, id = 887379146857144461) #Currently a test role, replace id with correct Verified role when added to main server
		await member.add_roles(verifiedRole)
###########################################################################
@bot.event #Sends message and gif on user joining server
async def on_member_join(member):
	cursor, conn = dbconnect() #Opens connection to db

	sql = ("SELECT setting_value FROM guild_settings WHERE (guild_id = %s AND setting = %s)")
	cursor.execute(sql, (member.guild.id, "welcome_channel"))
	result = cursor.fetchone()
	
	if result is not None: #Custom channel exists
		channel = member.guild.get_channel(int(result[0]))
	else: #System channel
		channel = member.guild.system_channel

	sql = ("SELECT setting_value FROM guild_settings WHERE (guild_id = %s AND setting = %s)")
	cursor.execute(sql, (member.guild.id, "welcome_status"))
	result = cursor.fetchone()
    
	if result is None or result[0] == "True": #welcome_status does not exist or is true
		sql = ("SELECT setting_value FROM guild_settings WHERE (guild_id = %s AND setting = %s)")
		cursor.execute(sql, (member.guild.id, "welcome_msg"))
		result = cursor.fetchone()
		
		if result is None: #Custom welcome message does not exist
			message = "Welcome %s to the server!"
		else: #Custom message does exist
			message = result[0]
		
		sql = ("SELECT setting_value FROM guild_settings WHERE (guild_id = %s AND setting = %s)")
		cursor.execute(sql, (member.guild.id, "welcome_picture"))
		result = cursor.fetchone()
		
		if result is None: #Default url
			url = "https://media.tenor.co/images/3ccff8c4b2443d93811eac9b2fd56f11/raw"
		else: #Custom url for image
			url = result[0]
        
		await channel.send(message %member.mention)
		embed = discord.Embed()
		embed.set_image(url = url)
		await channel.send(embed = embed)
	conn.close() #Closes connection to db
###########################################################################
@bot.event #Sends a message when someone leaves the server
async def on_member_remove(member):
    cursor, conn = dbconnect() #Opens connection to db
    
    sql = ("SELECT setting_value FROM guild_settings WHERE (guild_id = %s AND setting = %s)")
    cursor.execute(sql, (member.guild.id, "leave_channel"))
    result = cursor.fetchone()
    if result is not None:
        channel = member.guild.get_channel(int(result[0]))
    else:
        channel = member.guild.system_channel

    sql = ("SELECT setting_value FROM guild_settings WHERE (guild_id = %s AND setting = %s)")
    cursor.execute(sql, (member.guild.id, "leave_status"))
    result = cursor.fetchone()
    
    if result is None or result[0] == "True": #welcome_status does not exist or is true
        sql = ("SELECT setting_value FROM guild_settings WHERE (guild_id = %s AND setting = %s)")
        cursor.execute(sql, (member.guild.id, "leave_msg"))
        result = cursor.fetchone()
        if result is None: #Custom welcome message does not exist
            message = "Adios **%s**..."
        else: #Custom message does exist
            message = result[0]
        sql = ("SELECT setting_value FROM guild_settings WHERE (guild_id = %s AND setting = %s)")
        cursor.execute(sql, (member.guild.id, "leave_picture"))
        result = cursor.fetchone()
        if result is None: #Default url
            url = "https://media.giphy.com/media/26u4b45b8KlgAB7iM/giphy.gif?cid=790b7611485e4b17dd30b01e42eae6ed2568acb8d39c1e23&rid=giphy.gif&ct=g"
        else: #Custom url for image
            url = result[0]
        await channel.send(message %member)
        embed = discord.Embed()
        embed.set_image(url = url)
        await channel.send(embed = embed)
    conn.close() #Closes connection to db
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
