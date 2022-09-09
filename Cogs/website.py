import asyncio
import json
import discord
from configparser import ConfigParser
import os
from datetime import datetime
from dateutil import parser
import httpx
from discord.ext import commands, bridge

CalendarNames = ["General", "League of Legends", "Valorant", "Rainbow 6", "Overwatch", "CS:GO", "Smite", "Rocket League", "DotA 2", "Call of Duty", "Apex Legends"]
GameOptions = []
for label in CalendarNames:
    GameOptions.append(discord.SelectOption(label=label))

class Website(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    ###########################################################################
    @discord.slash_command(description = "Creates a new event on the website calendar.")
    @commands.has_any_role('Board Member', 'Game Officer', 'Bot Technician', 'Mod', 'Faculty Advisor')
    async def createevent(
        self,
        ctx,
        name:discord.Option(str, "Enter the name of the event"),
        location:discord.Option(str, "Enter the location of the event"),
        game:discord.Option(str, "Choose what calendar this event should be on", choices = CalendarNames),
        date:discord.Option(str, "Enter the date (MM/DD/YY)"),
        time:discord.Option(str, "Enter the time")
    ):
        await ctx.defer()
        logEmbed = discord.Embed(title = "New Event", color = discord.Color.teal())

        try:
            datestring = f"{date} {time}"
            start = parser.parse(datestring, fuzzy=True)
        except ValueError:
            await ctx.respond(embed = discord.Embed(title = "Invalid date format", description = "Make sure your date is Month/Day/Year and your time is valid 12 hour time", color = discord.Color.red()))
            return

        calendar = game

        data = {
            "Title": name,
            "Location": location,
            "Calendar": calendar,
            "Start": start.isoformat()
        }
        status = await sendPost("NewEvent", data)

        if(status == 200):
            print(f"{ctx.user.name} Created an event {name} on calendar {calendar}")
            logEmbed.add_field(name=("*Name*"),value = name, inline=False)
            logEmbed.add_field(name=("*Location*"),value = location, inline=False)
            logEmbed.add_field(name=("*Calendar*"),value = calendar, inline=False)
            logEmbed.add_field(name=("*Starts*"),value = start.isoformat(), inline=False)

            await ctx.respond(embed = logEmbed)
        else:
            await ctx.respond(content = "Failed to create event")


    @createevent.error
    async def createevent_error(self, ctx, error):
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
    @discord.slash_command(description = "Changes the Inhouse Schedule for a game")
    @commands.has_any_role('Board Member', 'Game Officer', 'Bot Technician', 'Mod', 'Faculty Advisor')
    async def changeinhouse(self, ctx):
        await ctx.respond("Select the new Inhouse time and date", view=InhouseView())
###########################################################################
DayOfWeek = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
DayOptions = []
for label in DayOfWeek:
    DayOptions.append(discord.SelectOption(label=label))

TimeLabels = ["8:00am", "9:00am","10:00am","11:00am","12:00pm","1:00pm","2:00pm","3:00pm","4:00pm","5:00pm","6:00pm","7:00pm","8:00pm","9:00pm","10:00pm"]
TimeOptions = []
for label in TimeLabels:
    TimeOptions.append(discord.SelectOption(label=label))

class InhouseView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.game = ""
        self.day = -1
        self.time = ""

    @discord.ui.select( # the decorator that lets you specify the properties of the select menu
        row = 0,
        placeholder = "Choose a Game", # the placeholder text that will be displayed if nothing is selected
        min_values = 1,
        max_values = 1,
        options = GameOptions
    )
    async def game_select_callback(self, select, interaction): # the function called when the user is done selecting options
        self.game = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(
        row = 1,
        placeholder = "Choose a Day of the Week",
        min_values = 1,
        max_values = 1,
        options = DayOptions
    )
    async def day_select_callback(self, select, interaction):
        self.day = DayOfWeek.index(select.values[0])
        await interaction.response.defer()

    @discord.ui.select(
        row = 2,
        placeholder = "Choose a Time of Day",
        min_values = 1,
        max_values = 1,
        options = TimeOptions
    )
    async def time_select_callback(self, select, interaction):
        self.time = select.values[0]
        await interaction.response.defer()

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm_callback(self, button, interaction):
        complete = True
        for child in self.children: # loop through all the children of the view
            if(hasattr(child, "values") and len(child.values) == 0):
                complete = False

        if complete:
            data = {
                "Game": self.game,
                "FirstDay": datetime.utcnow().isoformat(),
                "StartTime": datetime.strptime(self.time, "%I:%M%p").isoformat(),
                "DayOfWeek": self.day
            }

            status = await sendPost("NewInhouse", data)
            if(status == 200):
                print(f"{interaction.user.name} changed {self.game} Inhouses to {DayOfWeek[self.day]}s at {self.time}")
                await interaction.message.edit(content = f"Changed {self.game} Inhouses to {DayOfWeek[self.day]}s at {self.time}", view = None)
            else:
                await interaction.message.edit(content = f"Failed to change Inhouse time, please try again or contact the Devs", view = None)
        else:
            await interaction.message.edit(content = "Select the new Inhouse time and date. (Fill in all fields!)")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel_callback(self, button, interaction):
        await interaction.message.delete()

###########################################################################
async def sendPost(endpoint, json):
    try: #Config var in Heroku
        headertext = f'apikey {os.environ["APIKEY"]}&name {os.environ["BOT_NAME"]}'
        host = os.environ["WEBSITE_IP"]
    except: #Runs from system
        config_object = ConfigParser()
        config_object.read("BotVariables.ini")
        variables = config_object["variables"]
        headertext = f'apikey {variables["APIKEY"]}&name {variables["BOT_NAME"]}'
        host = variables["WEBSITE_IP"]

    headers = {"Authorization" : headertext}
    async with httpx.AsyncClient(verify = False) as client:
        resp = await client.post(f'https://{host}/api/{endpoint}', json = json, headers = headers)
        print(resp)
        try:
            print(resp.json())
        except ValueError:
            return resp.status_code
        return resp.status_code
###########################################################################
def setup(bot):
    bot.add_cog(Website(bot))
