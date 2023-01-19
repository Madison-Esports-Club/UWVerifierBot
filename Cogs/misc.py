import asyncio
import json
import discord
from discord.ext import commands
from Cogs.Helpers.types import HelpTypes

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
###########################################################################
    @discord.slash_command(name = "help", debug_guilds=[887366492730036276]) #Help messages
    async def help(self, ctx, category: discord.Option(HelpTypes, "Enter the type of command", required = False)):
        if category == None: # Short version
            with open("UWVerificationHelp.json", "r") as helpFile:
                data = json.load(helpFile)
            data = data['short']

            embed = discord.Embed(title = "Help Menu\t\tPrefix: !", color=discord.Color.green())
            embed.set_author(name = "Type `/help [category]` to see an in-depth guide for the inputed category")
            embed.set_footer(text = "Created by DMLooter#4251 & PureCache#0001")
            embed.add_field(name = "Verification Commands", value = data["Verification"], inline = False)
            embed.add_field(name = "Website Commands", value = data["Website"], inline = False)
            embed.add_field(name = "Miscellaneous Commands", value = data["Misc"], inline = False)

        else: # Full version
            with open("UWVerificationHelp.json", "r") as helpFile:
                data = json.load(helpFile)

            data = data["full"]
            data = data[category.value.lower()]
            embed = discord.Embed(title = (f"{category} commands:"), color = discord.Color.green())
            embed.set_author(name=("Key: (required) [optional]"))
            embed.set_footer(text = "Created by DMLooter#4251 & PureCache#0001")

            for key in data:
                embed.add_field(name = (f"`{key}`"), value = data[key], inline = False)

        await ctx.respond(embed=embed)

    @help.error
    async def clear_error(self, ctx, error):
        await ctx.respond(embed = discord.Embed(title = "This category does not exist! Make sure you spelled it correctly, use `/help` to see a short list of all types"))
###########################################################################
    @discord.slash_command(name = "ping", debug_guilds=[887366492730036276])
    async def ping(self, ctx):
        try:
            embed = discord.Embed(title = "**Ping :ping_pong:**", color = discord.Color.blurple())
            embed.add_field(name= "Quick Estimate", value = f"{round(self.bot.latency*1000,2)} ms")

            tests = 300
            latencyList = []
            for x in range(tests):
                latencyList.append(self.bot.latency)

            embed.add_field(name = "Average", value=f"{round((sum(latencyList)/tests) * 1000, 2)} ms", inline = False)
            await ctx.respond(embed = embed)
        except Exception as e:
            print(e)
###########################################################################
    @discord.slash_command(name = "purge", debug_guilds=[887366492730036276]) #Clears previous x amount of messages (x between 1 & 50)
    @commands.has_guild_permissions(manage_messages = True)
    async def purge(self, ctx, limit: discord.Option(discord.SlashCommandOptionType.integer, "Amount of messages to clear (1-50)", required = True)):
        # Currently disabled b/c ctx.message.channel no longer exists and can't find alternative
        await ctx.respond(embed = discord.Embed(title = "Command currently disabled")) 
        return
        
        if limit > 50 or limit < 1:
            await ctx.respond(embed = discord.Embed(title = "Only 1 to 50 messages can be cleared at a time"))
            return
        try:
            await ctx.message.channel.purge(limit = (limit + 1)) #To account for the deletion message itself
            msg = await ctx.respond(embed = discord.Embed(title = f"Previous {limit} messages deleted"))
            await asyncio.sleep(2)
            await msg.delete()
        except discord.Forbidden:
           await ctx.respond(embed = discord.Embed(title = "I do not have enough permissions to do this, please change my role permissions!"))
        except Exception as e:
            print(e)
    @purge.error
    async def clear_error(self, ctx, error):
        if isinstance(error,commands.MissingPermissions):
            await ctx.respond(embed = discord.Embed(title = "You do not have permission to use this command"))
        elif isinstance(error, commands.BadArgument):
            await ctx.respond(embed = discord.Embed(title = "Parameter must be an integer between 1 and 50"))
        elif isinstance(error,commands.MissingRequiredArgument):
            await ctx.respond(embed = discord.Embed(title = "Missing required argument, use !purge x"))
###########################################################################
    @discord.slash_command(name = "botinfo", debug_guilds=[887366492730036276]) #Displays information about the bot
    async def botinfo(self, ctx):
        infoDict = {
                "Created": "September 2021"
                ,"Language": "Python 3.8.1"
                ,"Open Source GitHub": "https://github.com/Madison-Esports-Club/UWVerifierBot"
                }
        infoEmbed = discord.Embed(title = "UW Verification Bot Information", color = discord.Color.orange())
        infoEmbed.set_author(name = "Created by DMLooter#4251 & PureCache#0001")

        for key in infoDict:
            infoEmbed.add_field(name = key,value = infoDict[key], inline = False)
        await ctx.respond(embed = infoEmbed)
###########################################################################
def setup(bot):
    bot.add_cog(Misc(bot))
