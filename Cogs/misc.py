import asyncio
import json
import discord
from discord.ext import commands

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
###########################################################################
    @commands.command(name = "help", aliases = ["h", "helpinfo"]) #Help messages
    async def help(self, ctx, type = None):
        if type == None:
            with open("UWVerificationHelp.json", "r") as helpFile:
                data = json.load(helpFile)
            data = data['short']

            embed = discord.Embed(title = "Help Menu\t\tPrefix: !", color=discord.Color.green())
            embed.set_author(name = "Type `!help [category]` to see an in-depth guide for the inputed category")
            embed.set_footer(text = "Created by DMLooter#4251 & PureCache#0001")
            embed.add_field(name = "Verification Commands", value = data["Verification"], inline = False)
            embed.add_field(name = "Miscellaneous Commands", value = data["Misc"], inline = False)
            #embed.add_field(name = "Settings Commands", value = data["Settings"], inline = False)

        else:
            with open("UWVerificationHelp.json", "r") as helpFile:
                data = json.load(helpFile)

            data = data["full"]
            data = data[type.lower()]
            embed = discord.Embed(title = (f"{type} commands:"), color = discord.Color.green())
            embed.set_author(name=("Key: (required) [optional]"))
            embed.set_footer(text = "Created by DMLooter#4251 & PureCache#0001")

            for key in data:
                embed.add_field(name = (f"`{key}`"), value = data[key], inline = False)

        await ctx.send(embed=embed)

    @help.error
    async def clear_error(self, ctx, error):
        await ctx.send(embed = discord.Embed(title = "This category does not exist! Make sure you spelled it correctly, use `!help` to see a short list of all types"))
###########################################################################
    @commands.command(name = "ping")
    async def ping(self, ctx):
        try:
            embed = discord.Embed(title = "**Ping :ping_pong:**", color = discord.Color.blurple())
            embed.add_field(name= "Quick Estimate", value = f"{round(self.bot.latency*1000,2)} ms")

            tests = 300
            latencyList = []
            for x in range(tests):
                latencyList.append(self.bot.latency)

            embed.add_field(name = "Average", value=f"{round((sum(latencyList)/tests) * 1000, 2)} ms", inline = False)
            await ctx.send(embed = embed)
        except Exception as e:
            print(e)
###########################################################################
    @commands.command(name = "changelog", aliases = ["changes", "updates"]) #Displays bot's change log
    async def changelog(self, ctx):
        logEmbed = discord.Embed(title = "UW Verification Bot Change Log", color = discord.Color.teal())

        with open("UWVerificationHelp.json","r") as logFile:
            data = json.load(logFile)
        data = data["changeLog"]
        for key in data:
            logEmbed.add_field(name=("*" + key + "*"),value = data[key],inline=False)

        await ctx.send(embed = logEmbed)
###########################################################################
    @commands.command(name = "purge", aliases = ["clear", "delete"]) #Clears previous x amount of messages (x between 1 & 50)
    @commands.has_guild_permissions(manage_messages = True)
    async def purge(self, ctx, limit: int):
        if limit > 50 or limit < 1:
            await ctx.send(embed = discord.Embed(title = "Only 1 to 50 messages can be cleared at a time"))
            return
        try:
            await ctx.message.channel.purge(limit = (limit + 1))
            msg = await ctx.send(embed = discord.Embed(title = f"Previous {limit} messages deleted"))
            await asyncio.sleep(2)
            await msg.delete()
        except discord.Forbidden:
           await ctx.send(embed = discord.Embed(title = "I do not have enough permissions to do this, please change my role permissions!"))

    @purge.error
    async def clear_error(self, ctx, error):
        if isinstance(error,commands.MissingPermissions):
            await ctx.send(embed = discord.Embed(title = "You do not have permission to use this command"))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(embed = discord.Embed(title = "Parameter must be an integer between 1 and 50"))
        elif isinstance(error,commands.MissingRequiredArgument):
            await ctx.send(embed = discord.Embed(title = "Missing required argument, use !purge x"))
###########################################################################
    @commands.command(name = "botinfo", aliases = ["info"]) #Displays informaton about the bot
    async def botinfo(self, ctx):
        infoDict = {
                "Created": "September 2021"
                ,"Language": "Python 3.8.1"
                ,"Open Source GitHub": "https://github.com/Madison-Esports-Club/UWVerifierBot"
                }
        infoEmbed = discord.Embed(title = "UW Verification Bot Information", color = discord.Color.orange())
        infoEmbed.set_author(name = "Created by DMLooter#4251 & PureCache#0001")
        infoEmbed.set_footer(text = "Prefix: !")

        for key in infoDict:
            infoEmbed.add_field(name = key,value = infoDict[key], inline = False)
        await ctx.send(embed = infoEmbed)
###########################################################################
def setup(bot):
    bot.add_cog(Misc(bot))
