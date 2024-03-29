from configparser import ConfigParser
import os
import httpx
import datetime
from discord import utils
import asyncio
import hashlib
from mailchimp_marketing import Client
from mailchimp_marketing.api_client import ApiClientError

from typing import Union

# TODO Move this to external file to either
GameNames = ["League of Legends", "Valorant", "Rainbow Six Seige", "Overwatch", "CS:GO", "Smite", "Rocket League", "DotA 2", "Call of Duty", "Apex Legends"]

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
        print(f'{url}: {resp}')
        try:
            print(f'{url}: {resp.json()}')
        except ValueError:
            return resp.status_code, None
        return resp.status_code, resp.json()["value"]
###############################################################################
async def sendMailchimp(email, status) -> bool:
    config_object = ConfigParser()
    config_object.read("BotVariables.ini")
    variables = config_object["variables"]

    mailchimp = Client()
    mailchimp.set_config({
    "api_key": variables["MAILCHIMP_API"],
    "server": "us21"
    })

    list_id = variables["MAILCHIMP_LIST_ID"]

    member_info = {
        "email_address": email,
        "status_if_new": status,
        "status": status
    }
    member_email_hash = hashlib.md5(email.encode('utf-8').lower()).hexdigest()

    try:
        response = mailchimp.lists.set_list_member(list_id, member_email_hash, member_info)
        print(f"Updated {email} to {response['status']}")
        return True
    except ApiClientError as error:
        print(f"An exception occurred while updating email {email} to {status}: {error}")
        return False
###############################################################################
class Team():
    def __init__(self, json):
        self.id = json["id"]
        self.name = json["name"]

    def __str__(self):
        return self.name

class Player():
    def __init__(self, json):
        self.id = json["id"]
        self.name = json["name"]
        self.tag = json["screenName"]
        if("iconURL" in json):
            self.iconURL= json["iconURL"]
        else:
            self.iconURL = None

    def __str__(self):
        return f"{self.tag} - {self.name}"

    def load(self, json):
        self.id = json["id"]
        self.name = json["name"]
        self.tag = json["screenName"]
        self.year = json["year"]
        self.major = json["major"]
        if("iconURL" in json):
            self.iconURL= json["iconURL"]
        else:
            self.iconURL = None

class PlayerCache():
    """
    Creates a new cache of players from the website.

    refresh is the amount of time after which the cache is purged and
    all new data is pulled from the website
    """
    def __init__(self, refresh: datetime.timedelta) -> None:
        self.players: list[Player] = []
        self.last_updated = datetime.datetime.min
        self.refresh_interval = refresh
        self.lock = asyncio.Lock()

    async def update_cache(self):
        # Do thread safety
        async with self.lock:
            if(self.last_updated + self.refresh_interval < datetime.datetime.now() ):
                endpoint = "GetPlayers"

                status, data = await sendPost(endpoint)

                if(status == 200):
                    self.last_updated = datetime.datetime.now() # only update if it succeeded.
                    self.players = []

                    if(len(data) > 0):
                        print(f"Caching {len(data)} Players")
                        for playersData in data:
                            self.players.append(Player(playersData))
                    else:
                        print("Warning: No Players retrieved into cache")
                else:
                    print("Error: Failed retrieving Players into cache")

    async def get_all_players(self) -> list[Player]:
        await self.update_cache()

        return self.players

    async def get_by_name(self, name:str) -> Union[Player, None]:
        await self.update_cache()
        return utils.get(self.players, name=name)

    async def get_by_tag(self, tag:str) -> Union[Player, None]:
        await self.update_cache()
        return utils.get(self.players, tag=tag)

    """
    Attempts to find a player with the specified text. First checks names, then tags, then "tag - name".
    """
    async def find(self, text:str) -> Union[Player, None]:
        await self.update_cache()

        out = utils.get(self.players, name=text)
        if out != None:
            return out

        out = utils.get(self.players, tag=text)
        if out != None:
            return out

        for player in self.players:
            if text == f"{player.tag} - {player.name}":
                return player
        return None

    """
    Attempts to create a Player.

    If the server accepts the creation, the player is added to the cache and is returned
    Otherwise the failure message is returned.
    """
    async def create_player(self, name: str, tag: str, year: str, major: str, icon: Union[str, None] = None) -> Union[str, Player]:
        data = {
            "Name": name,
            "ScreenName": tag,
            "Year": year,
            "Major": major,
            "IconString": icon
        }
        status, response = await sendPost("NewPlayer", data)

        if(status == 200):
            player = Player({"id":response["id"], "name": name, "screenName":tag, "iconURL": response["icon"]})
            print(f"Player created: {player}")
            self.players.append(player)
            return player
        else:
            return "Failed to create Player" #TODO DUPLICATE MESSAGE
        #TODO maybe add duplicate checking

    """
    Attempts to delete a Player.

    If the server accepts the deletion, the player is removed from the cache and None is returned
    Otherwise the failure message is returned.
    """
    async def delete_player(self, player:Player) -> Union[str, None]:
        status, response = await sendPost(f"DeletePlayer?PlayerID={player.id}")

        if(status == 200):
            print(f"Player deleted: {player.name}")
            if(player not in self.players):
                return None
            try:
                self.players.remove(player)
            except ValueError:
                return None
            return None
        else:
            if(response['message'] == "Invalid Player ID"):
                return "Player does not exist"
            else:
                return "Failed to delete player, please try again or contact the Devs"

    """
    Attempts to edit a Player.

    If the server accepts the edit, the player is changed in the cache and None is returned
    Otherwise the failure message is returned.
    """
    async def edit_player(self, player: Player, name: Union[str, None], tag: Union[str, None], year: Union[str, None], major: Union[str, None], icon: Union[str, None]) -> Union[str, None]:
        data = { #TODO check nullability on the .NET side6
            "ID": player.id,
            "Name": name,
            "ScreenName": tag,
            "Year": year,
            "Major": major,
            "IconString": icon
        }
        status, response = await sendPost("EditPlayer", data) #edit player will return an entire player's data

        if(status == 200):
            player.load(response['player']) #Have to edit existing object
            print(f"Player edited: {player}")
            return None
        else:
            return "Failed to edit Player"
        #TODO maybe add duplicate checking

class TeamCache():
    """
    Creates a new cache of teams from the website.

    refresh is the amount of time after which the cache is purged and
    all new data is pulled from the website
    """
    def __init__(self, refresh: datetime.timedelta) -> None:
        self.teams: dict[str, list[Team]] = {}
        self.last_updated = datetime.datetime.min
        self.refresh_interval = refresh
        self.lock = asyncio.Lock()

    async def update_cache(self):
        # Do thread safety
        async with self.lock:
            if(self.last_updated + self.refresh_interval < datetime.datetime.now() ):
                for game in GameNames:
                    endpoint = f"GetTeams?GameName={game}"

                    status, data = await sendPost(endpoint)

                    if(status == 200):
                        self.last_updated = datetime.datetime.now() # only update if it succeeded.
                        self.teams[game] = []

                        if(len(data) > 0):
                            print(f"Caching {len(data)} Teams")
                            for teamData in data:
                                self.teams[game].append(Team(teamData))
                        else:
                            print("Warning: No Teams retrieved into cache")
                    else:
                        print(f"Error: Failed retrieving Teams into cache, {status}, {data}")

    """
    Removes the team from the specifed game
    Otherwise searches through all games
    returns True if a team was removed
    """
    async def remove_cached(self, team:Team, game:str) -> bool:
        if(game not in GameNames):
            return False

        try:
            self.teams[game].remove(team)
        except ValueError:
            return False
        return True

        return False

    async def get_all_teams(self, game:str) -> list[Team]:
        await self.update_cache()

        return self.teams[game]

    """
    If game is specified, returns a team with that id in that game
    Otherwise searches through all games
    returns None if no game matches the id
    """
    async def get_by_id(self, id:int, game:str = None) -> Union[Team, None]:
        await self.update_cache()
        if(game != None):
            return utils.get(self.teams[game], id=id)

        for gameName in GameNames:
            search = utils.get(self.teams[gameName], id=id)
            if search != None:
                return search

        return None

    """
    If game is specified, returns a team by that name in that game
    Otherwise searches through all games and returns the first matching game (may not be unique!!!!)
    returns None if no game matches the name
    """
    async def get_by_name(self, name:str, game:str = None) -> Union[Team, None]:
        await self.update_cache()
        if(game != None):
            return utils.get(self.teams[game], name=name)

        for gameName in GameNames:
            search = utils.get(self.teams[gameName], name=name)
            if search != None:
                return search

        return None

    """
    Attempts to create a Team.

    If the server accepts the creation, the team is added to the cache and None is returned
    Otherwise the failure message is returned.
    """
    async def create_team(self, name: str, game: str) -> Union[str, None]:
        # Cache duplicate checking
        if (await self.get_by_name(name, game)) != None:
            return "A team with that name already exists!"

        data = {
            "Name": name,
            "Game": game
        }
        status, response = await sendPost("NewTeam", data)

        if(status == 200):
            print(f"{game} team created: {name}")
            team = Team({"id":response["id"], "name": name})
            self.teams[game].append(team)
            return None
        else:
            if(response['message'] == 'Duplicate Team Name'):
                return "A team with that name already exists!" #TODO DUPLICATE MESSAGE
            else:
                return "Failed to create team"

    """
    Attempts to delete a Team.

    If the server accepts the deletion, the team is removed from the cache and None is returned
    Otherwise the failure message is returned.

    Must specify at least id or name, ideally name and game
    """
    async def delete_team(self, game: str, id: int = None, name: str = None) -> Union[str, None]:
        if(game == None):
            return "You must specify the game that the team is under."

        # Check it exists
        team = None
        if id != None:
            team = await self.get_by_id(id, game)
            if team == None:
                return "Cannot find a team with that id"
        elif name != None:
            team = await self.get_by_name(name, game)
            if team == None:
                return "Cannot find a team with that name"

        if team == None:
            return "Team name or id must be specified"

        status, response = await sendPost(f"DeleteTeam?TeamID={team.id}")

        if(status == 200):
            print(f"Team deleted: {team.name}")
            await self.remove_cached(team, game)
            return None
        else:
            if(response['message'] == "Invalid Team ID"):
                return "Team does not exist"
            else:
                return "Failed to delete team, please try again or contact the Devs"

async def add_email(email) -> bool:
    return await sendMailchimp(email, "subscribed")

async def remove_email(email) -> bool:
    return await sendMailchimp(email, "unsubscribed")
