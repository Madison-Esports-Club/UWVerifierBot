import asyncio
import json
import discord
from configparser import ConfigParser
import os
from datetime import datetime
import httpx
from discord.ext import commands

class Website(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
###########################################################################
    @discord.slash_command(description = "Creates a new event on the website calendar.", guild_ids = [887366492730036276])
    @commands.has_any_role('Board Member', 'Game Officer', 'Bot Technician', 'Mod', 'Faculty Advisor')
    async def create_event(self, ctx, name:discord.Option(str), location:discord.Option(str), game:discord.Option(str), date:discord.Option(str), time:discord.Option(str), ampm:discord.Option(str)):
        await ctx.defer()
        logEmbed = discord.Embed(title = "New Event", color = discord.Color.teal())

        try:
            start = datetime.strptime(f"{date} {time} {ampm}", "%m/%d/%y %I:%M %p")
        except ValueError:
            await ctx.respond(embed = discord.Embed(title = "Invalid date format", description = "Correct usage: !createevent \"<name>\" \"<location>\" \"<game>\" mm/dd/yy HH:MM AM/PM", color = discord.Color.red()))
            return

        calendar = parseGameToCalendar(game)
        if calendar == None:
            await ctx.respond(embed = discord.Embed(title = "Invalid Game Name", description = "Check your spelling on the game name! If you think it is correct please contact the devs.", color = discord.Color.red()))
            return

        data = {
            "Title": name,
            "Location": location,
            "Calendar": calendar,
            "Start": start.isoformat()
        }
        await sendPost("NewEvent", data) # TODO Add failure mode

        logEmbed.add_field(name=("*Name*"),value = name, inline=False)
        logEmbed.add_field(name=("*Location*"),value = location, inline=False)
        logEmbed.add_field(name=("*Calendar*"),value = calendar, inline=False)
        logEmbed.add_field(name=("*Starts*"),value = start.isoformat(), inline=False)

        await ctx.respond(embed = logEmbed)

    @create_event.error
    async def create_event_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.respond(embed = discord.Embed(title = "Missing required argument", description = "Correct usage: !createevent \"<name>\" \"<location>\" \"<description>\" mm/dd/yy HH:MM AM/PM", color = discord.Color.red()))
        elif isinstance(error, commands.MissingAnyRole):
            await ctx.respond(embed = discord.Embed(title = "Missing required permission", color = discord.Color.red()))
            print(f"non-admin {ctx.message.author} tried to use createevent")
        else:
            await ctx.respond(embed = discord.Embed(title = "Unknown error. Please contact developers to check logs", color = discord.Color.red()))
            print("Create Event error: ", error)
            raise error
###########################################################################
async def sendPost(endpoint, json):
    try: #Config var in Heroku
        headertext = f'apikey {os.environ["APIKEY"]}&name {os.environ["BOT_NAME"]}'
    except: #Runs from system
        config_object = ConfigParser()
        config_object.read("BotVariables.ini")
        variables = config_object["variables"]
        headertext = f'apikey {variables["APIKEY"]}&name {variables["BOT_NAME"]}'

    headers = {"Authorization" : headertext}
    async with httpx.AsyncClient() as client:
        resp = await client.post(f'https://madisonesports.club/api/{endpoint}', json = json, headers = headers)
        print(resp)
        try:
            print(resp.json())
        except ValueError:
            return
###########################################################################
LoLNames = ["lol", "league", "league of legends"]
ValorantNames = ["valorant","val"]
R6Names = ["Rainbow six", "rainbow 6", "rainbow six siege", "rainbow 6 siege", "r6", "r6 siege"]
OWNames = ["ow", "overwatch", "overwatch 2", "ow2"]
CSGONames = ["csgo","cs:go","cs","counterstrike","counter strike", "counterstrike global offensive", "counterstrike: global offensive"]
SmiteNames = ["smite"]
RLNames = ["rocket league", "rl"]
DotANames = ["dota", "dota2", "defense of the ancients", "defense of the ancients 2"]
CoDNames = ["cod", "call of duty"]
ApexNames = ["apex", "apex legends"]
NormalizeNames = [("General", ["general"]), ("League of Legends", LoLNames), ("Valorant", ValorantNames), ("Rainbow 6", R6Names), ("Overwatch", OWNames), ("CS:GO", CSGONames),("Smite", SmiteNames), ("Rocket League", RLNames), ("DotA 2", DotANames), ("Call of Duty", CoDNames),("Apex Legends", ApexNames)]
"""
Takes in a "game name" and attempts to normalize it to the full Calendar name
"""
def parseGameToCalendar(game):
    game = game.lower()
    for names in NormalizeNames:
        for name in names[1]:
            if(name == game):
                return names[0]
    return None
###########################################################################
def setup(bot):
    bot.add_cog(Website(bot))
