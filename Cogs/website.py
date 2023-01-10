import asyncio
import json
import discord
from configparser import ConfigParser
import os
from datetime import datetime, timedelta
from dateutil import parser
import httpx
from discord.ext import commands, bridge
from collections.abc import Callable, Awaitable

from Cogs.Helpers.autocompleteHelpers import create_player_autocomplete, create_team_autocomplete
from Cogs.Helpers.websiteHelpers import PlayerCache, TeamCache

team_cache = TeamCache(timedelta(0,120))
player_cache = PlayerCache(timedelta(0,120))

GameNames = ["League of Legends", "Valorant", "Rainbow Six Seige", "Overwatch", "CS:GO", "Smite", "Rocket League", "DotA 2", "Call of Duty", "Apex Legends"]
GameOptions = []
for label in GameNames:
    GameOptions.append(discord.SelectOption(label=label))

CalendarNames = ["General", "League of Legends", "Valorant", "Rainbow Six Seige", "Overwatch", "CS:GO", "Smite", "Rocket League", "DotA 2", "Call of Duty", "Apex Legends"]
CalendarOptions = []
for label in CalendarNames:
    CalendarOptions.append(discord.SelectOption(label=label))

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
        time:discord.Option(str, "Enter the time (12 hour, am/pm) ")
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
        status, response = await sendPost("NewEvent", data)

        if(status == 200):
            print(f"{ctx.user.name} Created an event {name} on calendar {calendar}")
            logEmbed.add_field(name=("*Name*"),value = name, inline=False)
            logEmbed.add_field(name=("*Location*"),value = location, inline=False)
            logEmbed.add_field(name=("*Calendar*"),value = calendar, inline=False)
            logEmbed.add_field(name=("*Starts*"),value = start.strftime("%m/%d/%Y %-I:%M %p"), inline=False)

            await ctx.respond(embed = logEmbed)
        else:
            await ctx.respond(content = "Failed to create event")


    @createevent.error
    async def createevent_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.respond(embed = discord.Embed(title = "Missing required argument", description = "Correct usage: /createevent \"<name>\" \"<location>\" \"<game>\" <mm/dd/yy> <HH:MM AM/PM>", color = discord.Color.red()))
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
    @discord.slash_command(description = "Deletes an event from the website calendar.", debug_guilds=[887366492730036276])
    @commands.has_any_role('Board Member', 'Game Officer', 'Bot Technician', 'Mod', 'Faculty Advisor')
    async def deleteevent(
        self,
        ctx,
        calendar:discord.Option(str, "Choose what calendar you want to delete an event from", choices = CalendarNames)
    ):
        await ctx.defer()
        logEmbed = discord.Embed(title = "Get Event", color = discord.Color.teal())

        status, data = await sendPost(f"GetEvents?Calendar={calendar}")

        if(status == 200):
            if(len(data) > 0):
                events = []
                for eventData in data:
                    events.append(Event(eventData)) # TODO truncate to 25

                await ctx.respond("Select the event to delete", view=DeleteEventView(events))
            else:
                await ctx.respond(content = "No upcoming events on that calendar")
        else:
            await ctx.respond(content = "Failed to get events")

    @deleteevent.error
    async def deleteevent_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.respond(embed = discord.Embed(title = "Missing required argument", description = "Correct usage: /deleteevent \"<calendar>\"", color = discord.Color.red()))
        elif isinstance(error, commands.MissingAnyRole):
            await ctx.respond(embed = discord.Embed(title = "Missing required permission", color = discord.Color.red()))
            print(f"non-admin {ctx.message.author} tried to use deleteevent")
        else:
            await ctx.respond(embed = discord.Embed(title = "Unknown error. Please contact developers to check logs", color = discord.Color.red()))
            print("Delete Event error: ", error)
            raise error
###################################################################################
    @discord.slash_command(description = "Creates a Team on the Website", debug_guilds=[887366492730036276], guild_ids=[887366492730036276])
    @commands.has_any_role('Board Member', 'Game Officer', 'Bot Technician', 'Mod', 'Faculty Advisor')
    async def createteam(
        self,
        ctx,
        game:discord.Option(str, "Choose what game you want to create a team for", choices = GameNames),
        name:discord.Option(str, "Enter the name of the team to create")
    ):
        await ctx.defer()
        logEmbed = discord.Embed(title = "New Team", color = discord.Color.teal())
        resp = await team_cache.create_team(name, game)

        if(resp == None):
            print(f"{ctx.user.name} Created a {game} team: {name}")
            logEmbed.add_field(name=("*Name*"),value = name, inline=False)
            logEmbed.add_field(name=("*Game*"),value = game, inline=False)

            await ctx.respond(embed = logEmbed)
        else:
            await ctx.respond(content = resp)

    @createteam.error
    async def createteam_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.respond(embed = discord.Embed(title = "Missing required argument", description = "Correct usage: /createteam \"<game>\" \"<name>\"", color = discord.Color.red()))
        elif isinstance(error, commands.MissingAnyRole):
            await ctx.respond(embed = discord.Embed(title = "Missing required permission", color = discord.Color.red()))
            print(f"non-admin {ctx.message.author} tried to use createteam")
        else:
            await ctx.respond(embed = discord.Embed(title = "Unknown error. Please contact developers to check logs", color = discord.Color.red()))
            print("Create Team error: ", error)
            raise error
###################################################################################
    @discord.slash_command(description = "Deletes a Team from the Website", debug_guilds=[887366492730036276], guild_ids=[887366492730036276])
    @commands.has_any_role('Board Member', 'Game Officer', 'Bot Technician', 'Mod', 'Faculty Advisor')
    async def deleteteam(self, ctx):
        await ctx.defer()

        async def delete_team_callback(gameName:str, team:Team, interaction:discord.Interaction) -> None:
            status, response = await sendPost(f"DeleteTeam?TeamID={team.id}", None)
            if(status == 200):
                print(f"{interaction.user.name} deleted {gameName} Team {team.name}")
                await interaction.message.edit(content = f"Deleted {gameName} Team {team.name}", view = None)
            else:
                if(response['message'] == "Invalid Team ID"):
                    await interaction.message.edit(content = f"Team does not exist", view = None)
                else:
                    await interaction.message.edit(content = f"Failed to delete team, please try again or contact the Devs", view = None)
        
        await ctx.respond("Select the Team to delete", view=GameTeamView(action = delete_team_callback))
    
    @deleteteam.error
    async def deleteteam_error(self, ctx, error):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.respond(embed = discord.Embed(title = "Missing required permission", color = discord.Color.red()))
            print(f"non-admin {ctx.message.author} tried to use deleteteam")
        else:
            await ctx.respond(embed = discord.Embed(title = "Unknown error. Please contact developers to check logs", color = discord.Color.red()))
            print("Delete Team error: ", error)
            raise error
###########################################################################
    @discord.slash_command(description = "Creates a Player on the Website", debug_guilds=[887366492730036276], guild_ids=[887366492730036276])
    @commands.has_any_role('Board Member', 'Game Officer', 'Bot Technician', 'Mod', 'Faculty Advisor')
    async def createplayer(
        self,
        ctx,
        name:discord.Option(str, "Enter the real name of the player"),
        tag:discord.Option(str, "Enter the screen name of the player")
    ):
        await ctx.defer()
        logEmbed = discord.Embed(title = "New Player", color = discord.Color.teal())
        resp = await player_cache.create_player(name, tag)

        if(resp == None):
            print(f"{ctx.user.name} created a player: {name}, '{tag}'")
            logEmbed.add_field(name=("*Name*"),value = name, inline=False)
            logEmbed.add_field(name=("*Tag*"),value = tag, inline=False)

            await ctx.respond(embed = logEmbed)
        else:
            await ctx.respond(resp)

    @createplayer.error
    async def createplayer_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.respond(embed = discord.Embed(title = "Missing required argument", description = "Correct usage: /createplayer \"<name>\" \"<tag>\"", color = discord.Color.red()))
        elif isinstance(error, commands.MissingAnyRole):
            await ctx.respond(embed = discord.Embed(title = "Missing required permission", color = discord.Color.red()))
            print(f"non-admin {ctx.message.author} tried to use createplayer")
        else:
            await ctx.respond(embed = discord.Embed(title = "Unknown error. Please contact developers to check logs", color = discord.Color.red()))
            print("Create Player error: ", error)
            raise error
###########################################################################
    @discord.slash_command(description = "Adds a Player to a Team", debug_guilds=[887366492730036276], guild_ids=[887366492730036276])
    @commands.has_any_role('Board Member', 'Game Officer', 'Bot Technician', 'Mod', 'Faculty Advisor')
    async def addplayer(
        self,
        ctx: discord.context.ApplicationContext,
        game: discord.Option(str, "Choose what Game to look for Teams in", choices = GameNames),
        teamName: discord.Option(str, "Select the Team to add to", name="team",autocomplete=create_team_autocomplete(team_cache)),
        playerName: discord.Option(str, "Select the Player to add", name="player", autocomplete=create_player_autocomplete(player_cache))
    ):
        await ctx.defer()
        team = await team_cache.get_by_name(teamName, game)
        if team == None:
            await ctx.respond(f"Could not find a team named {teamName} for {game} (Try using the autocomplete!)")
            return
        
        player = await player_cache.find(playerName)
        if player == None:
            await ctx.respond(f"Could not find a player named {playerName} (Try using the autocomplete!)")
            return

        status, response = await sendPost(f"AddPlayerToTeam?TeamID={team.id}&PlayerID={player.id}", None)

        if(status == 200):
            print(f"{ctx.user} added {player} to {team}")
            await ctx.respond(f"Added Player {playerName} to {teamName}")
        else:
            if(response['message'] == "Player already on Team"):
                await ctx.respond(f"Player is already on team.")
            else:
                await ctx.respond(f"Failed to add player, please try again or contact the Devs")

    @addplayer.error
    async def addplayer_error(self, ctx: discord.context.ApplicationContext, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.respond(embed = discord.Embed(title = "Missing required argument", description = "Correct usage: /addplayer \"<game>\" \"<team>\" \"<player>\"", color = discord.Color.red()))
        elif isinstance(error, commands.MissingAnyRole):
            await ctx.respond(embed = discord.Embed(title = "Missing required permission", color = discord.Color.red()))
            print(f"non-admin {ctx.message.author} tried to use addplayer")
        else:
            await ctx.respond(embed = discord.Embed(title = "Unknown error. Please contact developers to check logs", color = discord.Color.red()))
            print("Add Player error: ", error)
            raise error
###########################################################################
    @discord.slash_command(description = "Removes a Player from a Team", debug_guilds=[887366492730036276], guild_ids=[887366492730036276])
    @commands.has_any_role('Board Member', 'Game Officer', 'Bot Technician', 'Mod', 'Faculty Advisor')
    async def removeplayer(self, ctx):
        await ctx.defer()

        async def remove_player_callback(gameName:str, team:Team, player:Player, interaction:discord.Interaction) -> None:
            status, response = await sendPost(f"RemovePlayerFromTeam?TeamID={team.id}&PlayerID={player.id}", None)
            if(status == 200):
                print(f"{interaction.user.name} removed {player.tag} from {team.name}")
                await interaction.message.edit(content = f"Removed Player {player.tag} from {team.name}", view = None)
            else:
                if(response['message'] == "Player not on Team"):
                    await interaction.message.edit(content = f"Player is already on team.", view = None)
                else:
                    await interaction.message.edit(content = f"Failed to remove player, please try again or contact the Devs", view = None)
        
        await ctx.respond("Select the Team and Player", view=GameTeamPlayerView(action = remove_player_callback, show_players_on_team = True, include_empty_teams=False))
    
    @removeplayer.error
    async def removeplayer_error(self, ctx, error):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.respond(embed = discord.Embed(title = "Missing required permission", color = discord.Color.red()))
            print(f"non-admin {ctx.message.author} tried to use removeplayer")
        else:
            await ctx.respond(embed = discord.Embed(title = "Unknown error. Please contact developers to check logs", color = discord.Color.red()))
            print("Remove Player error: ", error)
            raise error
###########################################################################
class EventDropdown(discord.ui.Select):
    def __init__(self, events):
        self.events = events
        self.event = None;
        self.selected = -1
        self.eventOptions = []
        for event in self.events:
            self.eventOptions.append(discord.SelectOption(label=event.title, value=str(event.id), description=event.start.strftime("%m/%d/%Y %-I:%M %p")))

        super().__init__(
            placeholder = "Choose an Event", # the placeholder text that will be displayed if nothing is selected
            min_values = 1,
            max_values = 1,
            options = self.eventOptions
        )

    async def callback(self, interaction: discord.Interaction):
        self.selected = self.values[0]
        self.event = discord.utils.get(self.events, id=int(self.selected))
        await interaction.response.defer()
###########################################################################
class DeleteEventView(discord.ui.View):
    def __init__(self, events):
        super().__init__()
        self.events = events
        self.dropdown = EventDropdown(events)

        self.add_item(self.dropdown)

    @discord.ui.button(row=1,label="Confirm", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm_callback(self, button, interaction):
        complete = True
        for child in self.children: # loop through all the children of the view
            if(hasattr(child, "values") and len(child.values) == 0):
                complete = False

        if complete:
            status, response = await sendPost(f"DeleteEvent?ID={self.dropdown.selected}", None)
            if(status == 200):
                print(f"{interaction.user.name} deleted event {self.dropdown.event.title}")
                await interaction.message.edit(content = f"Deleted event {self.dropdown.event.title}", view = None)
            else:
                await interaction.message.edit(content = f"Failed to delete event {self.dropdown.event.title}, please try again or contact the Devs", view = None)
        else:
            await interaction.message.edit(content = "Select the event to Delete.")

    @discord.ui.button(row=1,label="Cancel", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel_callback(self, button, interaction):
        await interaction.message.delete()

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

            status, response = await sendPost("NewInhouse", data)
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
class PlayerDropdown(discord.ui.Select):
    """
    Creates a dropdown with the specified list of players
    An action can be specified to be called when the value is changed.
    """
    def __init__(self, players:list["Player"], action:Callable[[discord.ui.View, "PlayerDropdown", discord.Interaction], Awaitable[None]] = None, row: int = None):
        self.players = players
        self.player = None
        self.selected = -1
        self.playerOptions = []
        for player in self.players:
            self.playerOptions.append(discord.SelectOption(label=f"{player.tag} - {player.name}", value=str(player.id)))
        
        self.action = action
        super().__init__(
            row = row,
            placeholder = "Choose a Player", 
            min_values = 1,
            max_values = 1,
            options = self.playerOptions
        )

    async def callback(self, interaction: discord.Interaction):
        self.selected = self.values[0]
        self.player:Player = discord.utils.get(self.players, id=int(self.selected))
        if(self.action != None):
            await self.action(self.view, self, interaction)
        else:
            await interaction.response.defer()
###########################################################################
class TeamDropdown(discord.ui.Select):
    """
    Creates a dropdown with the specified list of teams
    An action can be specified to be called when the value is changed.

    The default value Option is the id of the team that should be selected by default
    """
    def __init__(self, teams:list["Team"], action:Callable[[discord.ui.View, "TeamDropdown", discord.Interaction], Awaitable[None]] = None, row: int = None, defaultValue:int=-1):
        self.teams = teams
        self.team = discord.utils.get(teams, id=defaultValue)
        self.selected = defaultValue
        self.teamOptions = []
        for team in self.teams:
            self.teamOptions.append(discord.SelectOption(label=team.name, value=str(team.id),default = (team.id == defaultValue)))
        
        self.action = action
        super().__init__(
            row = row,
            placeholder = "Choose a Team",
            min_values = 1,
            max_values = 1,
            options = self.teamOptions
        )

    async def callback(self, interaction: discord.Interaction):
        self.selected = self.values[0]
        self.team:Team = discord.utils.get(self.teams, id=int(self.selected))
        if(self.action != None):
            await self.action(self.view, self, interaction)
        else:
            await interaction.response.defer()
###########################################################################
class GameDropdown(discord.ui.Select):
    """
    Creates a dropdown with the list of games supported.
    An action can be specified to be called when the value is changed.
    """
    def __init__(self, action:Callable[[discord.ui.View, "GameDropdown", discord.Interaction], Awaitable[None]] = None, row:int = None, defaultValue:str = None):
        self.action = action

        # If we have a default, we have to make a new set of options.
        options = GameOptions
        if defaultValue in GameNames:
            self.selected = defaultValue
            self.game = defaultValue
            options = []
            for label in GameNames:
                options.append(discord.SelectOption(label=label))
        
        super().__init__(
            row = row,
            placeholder = "Choose a Game", # the placeholder text that will be displayed if nothing is selected
            min_values = 1,
            max_values = 1,
            options = options
        )
        for option in self.options:
            if option.label == defaultValue:
                option.default = True

    async def callback(self, interaction: discord.Interaction):
        self.selected = self.values[0]
        self.game = self.values[0]
        if(self.action != None):
            await self.action(self.view, self, interaction)
        else:
            await interaction.response.defer()
###########################################################################
class ConfirmButton(discord.ui.Button):
    """
    Creates a confirm button which will perform the specified action when clicked
    if and only if all selects in the parentView have a value selected

    The action will receive the view this buttton is attached to, and the interaction that spawned it.
    """
    def __init__(self, action:Callable[[discord.ui.View, discord.Interaction], Awaitable[None]], row:int = None):
        self.action = action
        super().__init__(
            row = row,
            label="Confirm",
            style=discord.ButtonStyle.success,
            emoji="✅"
        )

    async def callback(self, interaction: discord.Interaction):
        complete = True
        for child in self.view.children: # loop through all the children of the view
            if(hasattr(child, "values")):
                if(len(child.values) > 0): # if theres a value, its fine
                    continue
                else: # otherwise we have to check if a default was set (WHY THE FUCK DOES DEFUALT NOT SHOW UP IN VALUES!!!HOW WOULD YOU KNOW WITHOUT LOOPING THROUGH THEM ALLL)
                    defaultValue = False
                    for opt in child.options:
                        if opt.default:
                            defaultValue = True
                            break
                    if not defaultValue:
                        complete = False

        if complete:
            await self.action(self.view, interaction)
        else:
            await interaction.response.defer()
###########################################################################
class CancelButton(discord.ui.Button):
    """
    Creates a cancel button which will close the current view when clicked
    """
    def __init__(self, row:int = None):
        super().__init__(
            row = row,
            label="Cancel",
            style=discord.ButtonStyle.danger,
            emoji="❌"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.message.delete()
###########################################################################
class GameTeamPlayerView(discord.ui.View):
    """
    Creates a view which shows 3 selects, one for game, one for team, one for player.
    Selecting a new value on any select will clear and repopulate the ones below

    Customization options:
    include_empty_teams: TODO
        Sets whether teams with no players will show up in the team selector
            e.g. if you are removing players, this should be false.
        Defaults to True
    
    show_players_on_team:
        Sets whether the player dropdown will show only players on the team or only those not on the team
            e.g. if you are removing players this should be true
            e.g. if you are adding players this should be false
        Defaults to False
    
    action:
        Callback to be called when all three values are filled out and confirm is pressed.
        Method should take 4 arguments and be async:
            action(Game:str, TeamID: int, PlayerID: int, interaction: discord.Interaction)

    """
    def __init__(self, action:Callable[[str, "Team", "Player", discord.Interaction], Awaitable[None]] = None, *, include_empty_teams=True, show_players_on_team = False):
        super().__init__()
        self.action = action
        self.includeEmptyTeams = include_empty_teams
        self.showTeamPlayers = show_players_on_team

        self.gameDropdown = GameDropdown(self.game_callback, 0)

        # Create a blank dropdown for when we need to clear it
        self.blankTeamDropdown = TeamDropdown([Team({"id":0,"name":"Placeholder"})], self.team_callback, 1)
        self.blankTeamDropdown.placeholder = "Select a Game First"
        self.blankTeamDropdown.disabled = True
        self.teamDropdown = self.blankTeamDropdown

        # Create a blank dropdown for when we need to clear it
        self.blankPlayerDropdown = PlayerDropdown([Player({"id":0,"name":"Placeholder","screenName":"Placeholder"})], None, 2)
        self.blankPlayerDropdown.placeholder = "Select a Team First"
        self.blankPlayerDropdown.disabled = True
        self.playerDropdown = self.blankPlayerDropdown

        self.add_item(self.gameDropdown)
        self.add_item(self.teamDropdown)
        self.add_item(self.playerDropdown)
        self.add_item(ConfirmButton(self.confirm_callback, 3))
        self.add_item(CancelButton(3))


    """
    Method to replace the game dropdown
    """
    def replace_game_dropdown(self, dropdown: GameDropdown):
        self.remove_item(self.gameDropdown)
        self.gameDropdown = dropdown
        self.add_item(self.gameDropdown)

    """
    Method to replace the team dropdown
    """
    def replace_team_dropdown(self, dropdown: TeamDropdown):
        self.remove_item(self.teamDropdown)
        self.teamDropdown = dropdown
        self.add_item(self.teamDropdown)

    """
    Method to replace the player dropdown
    """
    def replace_player_dropdown(self, dropdown: PlayerDropdown):
        self.remove_item(self.playerDropdown)
        self.playerDropdown = dropdown
        self.add_item(self.playerDropdown)

    """
    Callback for when a game is selected
    Attempts to load the teams and populate the team dropdown
    Clears out the Player dropdown
    """
    async def game_callback(self, view:discord.ui.View, gameDropdown: GameDropdown, interaction:discord.Interaction):
        self.replace_player_dropdown(self.blankPlayerDropdown)

        teams = []
        status, data = await sendPost(f"GetTeams?GameName={gameDropdown.game}")

        if(status == 200):
            self.replace_game_dropdown(GameDropdown(self.game_callback, 0, gameDropdown.game))

            if(len(data) > 0):
                for teamData in data:
                    teams.append(Team(teamData)) # TODO truncate to 25

                self.replace_team_dropdown(TeamDropdown(teams, self.team_callback, 1))

                await interaction.message.edit(content = f"Select a Team from {gameDropdown.game}", view = self)
            else:
                self.replace_team_dropdown(self.blankTeamDropdown)
                self.teamDropdown.placeholder = f"No Teams for {gameDropdown.game}"

                await interaction.response.edit_message(content = f"No Teams exist for {gameDropdown.game}", view = self)
                return
        else:
            await interaction.message.edit(content = f"Failed to get Teams, please try again or contact the Devs", view = None)
            return

        await interaction.response.defer()

    async def team_callback(self, view:discord.ui.View, teamDropdown: TeamDropdown, interaction:discord.Interaction):
        players = []
        endpoint = "GetPlayers"
        if self.showTeamPlayers:
            endpoint += f"?IncludeTeamID={int(teamDropdown.selected)}" # Removing players from team
        else:
            endpoint += f"?ExcludeTeamID={int(teamDropdown.selected)}" # Adding players to team
        
        status, data = await sendPost(endpoint)

        if(status == 200):
            self.replace_team_dropdown(TeamDropdown(teamDropdown.teams, self.team_callback, 1, int(teamDropdown.selected)))

            if(len(data) > 0):
                for playersData in data:
                    players.append(Player(playersData)) # TODO truncate to 25

                self.replace_player_dropdown(PlayerDropdown(players, None, 2))

                await interaction.response.edit_message(content = f"Select a Player", view = self)
            else:
                self.replace_player_dropdown(self.blankPlayerDropdown)
                self.playerDropdown.placeholder = f"No valid Players for {teamDropdown.team.name}"

                await interaction.response.edit_message(content = f"No valid Players for {teamDropdown.team.name}", view = self)
        else:
            await interaction.response.edit_message(content = f"Failed to get Players, please try again or contact the Devs", view = None)

    async def confirm_callback(self, view, interaction):
        if(self.action != None):
            await self.action(self.gameDropdown.selected, self.teamDropdown.team, self.playerDropdown.player, interaction)
        else:
            await interaction.response.edit_message(content="Done!", view=None)
###########################################################################
class GameTeamView(discord.ui.View):
    """
    Creates a view which shows 2 selects, one for game, one for team
    Selecting a new value on the game select will clear and repopulate the team select

    Customization options:
    include_empty_teams: TODO
        Sets whether teams with no players will show up in the team selector

        Defaults to True
    
    action:
        Callback to be called when both values are selected and confirm is pressed.
        Method should take 3 arguments and be async:
            action(Game:str, TeamID: int, interaction: discord.Interaction)

    """
    def __init__(self, action:Callable[[str, "Team", discord.Interaction], Awaitable[None]] = None, *, include_empty_teams=True):
        super().__init__()
        self.action = action
        self.includeEmptyTeams = include_empty_teams

        self.gameDropdown = GameDropdown(self.game_callback, 0)

        # Create a blank dropdown for when we need to clear it
        self.blankTeamDropdown = TeamDropdown([Team({"id":0,"name":"Placeholder"})], None, 1)
        self.blankTeamDropdown.placeholder = "Select a Game First"
        self.blankTeamDropdown.disabled = True
        self.teamDropdown = self.blankTeamDropdown

        self.add_item(self.gameDropdown)
        self.add_item(self.teamDropdown)
        self.add_item(ConfirmButton(self.confirm_callback, 2))
        self.add_item(CancelButton(2))

    """
    Method to replace the game dropdown
    """
    def replace_game_dropdown(self, dropdown: GameDropdown):
        self.remove_item(self.gameDropdown)
        self.gameDropdown = dropdown
        self.add_item(self.gameDropdown)

    """
    Method to replace the team dropdown
    """
    def replace_team_dropdown(self, dropdown: TeamDropdown):
        self.remove_item(self.teamDropdown)
        self.teamDropdown = dropdown
        self.add_item(self.teamDropdown)

    """
    Callback for when a game is selected
    Attempts to load the teams and populate the team dropdown
    """
    async def game_callback(self, view:discord.ui.View, gameDropdown: GameDropdown, interaction:discord.Interaction):
        teams = []
        status, data = await sendPost(f"GetTeams?GameName={gameDropdown.game}")

        if(status == 200):
            self.replace_game_dropdown(GameDropdown(self.game_callback, 0, gameDropdown.game))

            if(len(data) > 0):
                for teamData in data:
                    teams.append(Team(teamData)) # TODO truncate to 25

                self.replace_team_dropdown(TeamDropdown(teams, None, 1))

                await interaction.message.edit(content = f"Select a Team from {gameDropdown.game}", view = self)
            else:
                self.replace_team_dropdown(self.blankTeamDropdown)
                self.teamDropdown.placeholder = f"No Teams for {gameDropdown.game}"

                await interaction.response.edit_message(content = f"No Teams exist for {gameDropdown.game}", view = self)
                return
        else:
            await interaction.message.edit(content = f"Failed to get Teams, please try again or contact the Devs", view = None)
            return

        await interaction.response.defer()

    async def confirm_callback(self, view, interaction):
        if(self.action != None):
            await self.action(self.gameDropdown.selected, self.teamDropdown.team, interaction)
        else:
            await interaction.response.edit_message(content="Done!", view=None)
###########################################################################
async def sendPost(endpoint, json = None):
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
    url = f'https://{host}/api/{endpoint}'
    async with httpx.AsyncClient(verify = False) as client:
        resp = await client.post(url, json = json, headers = headers)
        #TODO check for auth failures
        try:
            print(f'{url}: {resp.json()}')
        except ValueError:
            return resp.status_code, None
        return resp.status_code, resp.json()["value"]
###########################################################################
def setup(bot):
    bot.add_cog(Website(bot))

class Event():
    def __init__(self, json):
        self.id = json["id"]
        self.title=json["title"]
        self.location = json["location"]
        self.start = parser.parse(json["start"])

class Team():
    def __init__(self, json):
        self.id = json["id"]
        self.name = json["name"]

class Player():
    def __init__(self, json):
        self.id = json["id"]
        self.name = json["name"]
        self.tag = json["screenName"]