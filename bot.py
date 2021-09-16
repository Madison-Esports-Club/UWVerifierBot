# bot.py
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
#TOKEN = os.getenv('DISCORD_TOKEN')
TOKEN = "ODg3MzY1MzQwMjM1OTY4NTQy.YUDFXw.fzU1VfltcQzvO4O1rGhOGoaQmac"

# 2
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
	print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='verify')
#@commands.not_has_role('verified')
async def verfiy(ctx, email):
	if(discord.utils.get(ctx.author.roles, name="Verified") != None):
		await ctx.send("you are already verified!")
		return
	#print(ctx.author.id)
	await verifyEmail(email, ctx.author, ctx.guild)
	response = "Thank you for submitting your verification request, it will be processed within 24 hours.\nPlease ensure anyone is allowed to send you DMs to get notified if your verification was successful."
	await ctx.send(response)

async def verifyEmail(email, member, guild):
	print("Verifying " + member.name + " with email: " + email + " in server: " + guild.name)
	await member.send("Your email " + email + " is now verified in " + guild.name)
	await addVerifiedRole(member.id, guild.id)

@bot.event
async def on_command_error(ctx, error):
	print(error.__dict__)
	raise error

async def addVerifiedRole(memberID, guildID):
	guild = discord.utils.get(bot.guilds, id = guildID)
	if(guild == None):
		print("invalid guildID: " + str(guildID))
		return

	member = discord.utils.get(guild.members, id = memberID)
	if(member == None):
		print("invalid memberID: " + str(memberID) + " for guild: " + guild.name)
		return

	role = discord.utils.get(guild.roles, name = "Verified")
	if(role == None):
		print("No Verified role found in guild: " + guild.name)
		return

	await member.add_roles(role)

bot.run(TOKEN)
