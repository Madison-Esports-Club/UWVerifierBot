"""
import asyncio
import json
import discord
import datetime
from discord.ext import commands

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
###########################################################################
    @commands.command(name = "createevent")
    @commands.has_any_role('Board Member', 'Game Officer', 'Bot Technician', 'Mod', 'Faculty Advisor')
    async def createevent(self, ctx, name, location, description):
        logEmbed = discord.Embed(title = "New Event", color = discord.Color.teal())

        channel = discord.utils.get(ctx.guild.voice_channels, name = location)
        if(channel):
            entity_type = 2
        else:
            channel = discord.utils.get(ctx.guild.stage_channels, name = location)
            if(channel):
                entity_type = 1
            else:
                entity_type = 3

        event = await ctx.guild.create_scheduled_event(
            name = name,
            entity_type = entity_type,
            channel_id = channel.id if channel else None,
            scheduled_start_time = datetime.datetime.utcnow()+datetime.timedelta(days=1),
            scheduled_end_time = datetime.datetime.utcnow()+datetime.timedelta(days=2),
            location=location,
            description = description
        )
        logEmbed.add_field(name=("*Name*"),value = event.name, inline=False)
        logEmbed.add_field(name=("*Description*"),value = event.description, inline=False)
        logEmbed.add_field(name=("*Location*"),value = event.location if event.entity_type.value == 3 else f'VC: {channel.name}', inline=False)
        logEmbed.add_field(name=("*Starts*"),value = event.scheduled_start_time.isoformat(), inline=False)

        await ctx.send(embed = logEmbed)

    @createevent.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed = discord.Embed(title = "Missing required argument", description = "Correct usage: !createevent \"<name>\" \"<location>\" \"<description>\"", color = discord.Color.red()))
        elif isinstance(error, commands.MissingAnyRole):
            await ctx.send(embed = discord.Embed(title = "Missing required permission", color = discord.Color.red()))
            print(f"non-admin {ctx.message.author} tried to use createevent")
        else:
            await ctx.send(embed = discord.Embed(title = "Unknown error. Please contact developers to check logs", color = discord.Color.red()))
            print("Create Event error: ", error, error.withtraceback())
###########################################################################
    @commands.command(name = "schedule_stream")
    @commands.has_any_role('Board Member', 'Game Officer', 'Bot Technician', 'Mod', 'Faculty Advisor')
    async def schedule_stream(self, ctx, game, twitch_channel, *, time):
        logEmbed = discord.Embed(title = "New Stream", color = discord.Color.teal())
        location = f"twitch.tv/{twitch_channel}"
        description = f"{ctx.author.name} is streaming {game} at twitch.tv/{twitch_channel}"

        event = await ctx.guild.create_scheduled_event(
            name = f"{ctx.author.name} streaming {game}",
            entity_type = 3,
            channel_id = None,
            scheduled_start_time = datetime.datetime.utcnow()+datetime.timedelta(days=1),
            scheduled_end_time = datetime.datetime.utcnow()+datetime.timedelta(days=2),
            location=location,
            description = description
        )
        logEmbed.add_field(name=("*Name*"),value = event.name, inline=False)
        logEmbed.add_field(name=("*Description*"),value = event.description, inline=False)
        logEmbed.add_field(name=("*Location*"),value = event.location, inline=False)
        logEmbed.add_field(name=("*Starts*"),value = time, inline=False)

        await ctx.send(embed = logEmbed)

    @createevent.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed = discord.Embed(title = "Missing required argument", description = "Correct usage: !schedule_stream \"<game>\" \"<twitch_channel>\" \"<time>\"", color = discord.Color.red()))
        elif isinstance(error, commands.MissingAnyRole):
            await ctx.send(embed = discord.Embed(title = "Missing required permission", color = discord.Color.red()))
            print(f"non-admin {ctx.message.author} tried to use schedule_stream")
        else:
            await ctx.send(embed = discord.Embed(title = "Unknown error. Please contact developers to check logs", color = discord.Color.red()))
            print("Schedule Stream error: ", error, error.withtraceback())
###########################################################################
def setup(bot):
    bot.add_cog(Events(bot))"""
