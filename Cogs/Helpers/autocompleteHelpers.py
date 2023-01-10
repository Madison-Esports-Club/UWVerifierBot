import discord

from collections.abc import Iterable, Callable

from Cogs.Helpers.websiteHelpers import PlayerCache, TeamCache

# TODO Move this to external file to either
GameNames = ["League of Legends", "Valorant", "Rainbow Six Seige", "Overwatch", "CS:GO", "Smite", "Rocket League", "DotA 2", "Call of Duty", "Apex Legends"]

def create_team_autocomplete(cache:TeamCache) -> Callable[[discord.AutocompleteContext], Iterable[str]]:

    async def team_autocomplete(ctx:discord.AutocompleteContext) -> Iterable[str]:
        _cache = cache
        teams = []
        if "game" in ctx.options and ctx.options["game"] in GameNames :
            teams = await cache.get_all_teams(ctx.options["game"])

        return [val.name for val in teams if ctx.value in val.name]
    
    return team_autocomplete

def create_player_autocomplete(cache:PlayerCache) -> Callable[[discord.AutocompleteContext], Iterable[str]]:
    async def player_autocomplete(ctx:discord.AutocompleteContext) -> Iterable[str]:
        _cache = cache
        players = await cache.get_all_players()

        return [f"{val.tag} - {val.name}" for val in players if ctx.value.lower() in f"{val.tag} - {val.name}".lower()]
    
    return player_autocomplete