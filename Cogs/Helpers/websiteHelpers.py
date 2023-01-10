from configparser import ConfigParser
import os
import httpx
import datetime
from discord import utils

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
        try:
            print(f'{url}: {resp.json()}')
        except ValueError:
            return resp.status_code, None
        return resp.status_code, resp.json()["value"]
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

    def __str__(self):
        return f"{self.tag} - {self.name}"

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
    
    async def update_cache(self):
        # Do thread safety

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

    async def add_player(name: str, tag: str) -> bool:
        pass

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
    
    async def update_cache(self):
        # Do thread safety

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
                    print("Error: Failed retrieving Teams into cache")
    
    async def get_all_teams(self, game:str) -> list[Team]:
        await self.update_cache()

        return self.teams[game]

    """
    If game is specified, returns a team by that name in that game
    Otherwise searches through all games
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

    async def add_team(name: str, game: str) -> bool:
        pass