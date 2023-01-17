import discord
from discord.commands import SlashCommandGroup
from discord.ext import commands
from asyncio import TimeoutError as asyncioTimeout
from pytz import timezone

from Cogs.db import dbconnect
from Cogs.Helpers.verificationHelpers import insert_verified_user_record, verify_user, get_verification_record

#verified_table_name = "verified_users"
#verification_attempt_table_name = "verification_requests"

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot=bot
###########################################################################
    @discord.slash_command(name='verify', description="Verifies a user for access to locked channels", debug_guilds=[887366492730036276])
    async def verify(
        self,
        ctx,
        email: discord.Option(str, "Enter your wisc.edu email", required = True),
        fullname: discord.Option(str, "Enter your full name", required = True)
    ):
        if(discord.utils.get(ctx.author.roles, name = "Verified") != None): # We could have this check the DB, would maybe cause issues with manually verified folks.
            await ctx.respond(embed = discord.Embed(title = "You are already verified!", description = "*If you believe this is an error, please message a board member*", color = discord.Color.red()))
            return

        await ctx.defer()

        #Trims parameters
        email = email.strip()
        fullname = fullname.strip()

        verified, message, color = verify_user(ctx.author.id, email)

        if verified: #Prompts user to enter name to finish verifying

            await insert_verified_user_record(ctx.author.id, email, fullname)
            role = discord.utils.get(ctx.guild.roles, name = "Verified")
            await ctx.author.add_roles(role)
            await ctx.respond(embed = discord.Embed(title = f"{ctx.author}, you have been successfully verified!", color = color))

        else: #Verification errored, or they have a verification record already in the DB, but lost the role
            await ctx.respond(embed = discord.Embed(title = "Error", description = message, color = color))

    @verify.error
    async def clear_error(self, ctx, error):
        await ctx.respond(embed = discord.Embed(title = "An error occured, please ping a Bot Technician", description = error, color = discord.Color.red()))
###########################################################################
    @discord.slash_command(name = 'whois', description = 'Outputs a user\'s name and email', debug_guilds=[887366492730036276])
    @commands.has_any_role('Board Member', 'Game Officer', 'Bot Technician', 'Mod', 'Faculty Advisor')
    async def whois(self, ctx, user: discord.Option(str, "Enter the user to look up (UserName#0000)", required = True)):
        if('#' not in user):
            return await ctx.respond(embed = discord.Embed(title = "Missing required argument", description = "Please include 4-digit discriminator (#0000)", color = discord.Color.red()))

        parts = user.split('#', 1)
        name_part = parts[0]
        discriminator_part = parts[1]

        member = discord.utils.get(ctx.guild.members,  name = name_part, discriminator = discriminator_part)
        if member is None:
            return await ctx.respond(embed = discord.Embed(title = "Unknown user", description = f"Could not find {user} in this server", color = discord.Color.red()))

        email, name, time = get_verification_record(member.id)
        if(email is None):
            return await ctx.respond(embed = discord.Embed(title = "Not Verified", description = f"{user} is not verified.", color = discord.Color.orange()))

        if(name is None):
            name = "*No name registered*"
        time = time.astimezone(timezone("America/Chicago"))
        timestamp = time.strftime("%m/%d/%Y, %I:%M %p %Z")
        recordEmbed = discord.Embed(title = "Verification Record", color = discord.Color.green())
        recordEmbed.add_field(name = ("*Name*"), value = name, inline=False)
        recordEmbed.add_field(name = ("*Email*"), value = email, inline=False)
        recordEmbed.add_field(name = ("*Time Verified*"), value = timestamp, inline=False)
        return await ctx.respond(embed = recordEmbed)

    @whois.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.respond(embed = discord.Embed(title = "Missing required argument", description = "Correct usage: !whois UserName#0000", color = discord.Color.red()))
        elif isinstance(error, commands.MissingAnyRole):
            await ctx.respond(embed = discord.Embed(title = "Missing required permission", color = discord.Color.red()))
            print(f"non-admin {ctx.message.author} tried to use whois")
        else:
            await ctx.respond(embed = discord.Embed(title = "Unknown error. Please contact developers to check logs", color = discord.Color.red()))
            print("Whois error: ", error)
###########################################################################
    #todo make this a subcommand of verify
    @discord.slash_command(name = "manualverify", description= "Manually gives a user verified status.", debug_guilds=[887366492730036276])
    @commands.has_any_role('Board Member', 'Game Officer', 'Bot Technician', 'Mod', 'Faculty Advisor')
    async def manualverify(
        self,
        ctx,
        member: discord.Option(discord.SlashCommandOptionType.user, "@ the user you wish to manually verify", required = True),
        email: discord.Option(discord.SlashCommandOptionType.string, "Enter the user's wisc.edu email", required = True),
        full_name: discord.Option(discord.SlashCommandOptionType.string, "Enter the user's full name", required = True)
    ):
        if member is None:
            return await ctx.respond(embed = discord.Embed(title = "Unknown user", description = f"Could not find {member} in this server", color = discord.Color.red()))

        if(discord.utils.get(member.roles, name = "Verified") != None):
            return await ctx.respond(embed = discord.Embed(title = f"{member} is already verified!", color = discord.Color.red()))

        insert_verified_user_record(member.id, email, full_name)
        role = discord.utils.get(ctx.guild.roles, name = "Verified")
        await member.add_roles(role)

        message = f"{member} has been successfully verified!"
        await ctx.respond(embed = discord.Embed(title = message, color = discord.Color.green()))

    @manualverify.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.respond(embed = discord.Embed(title = "Missing required argument", description = "Correct usage: !manualverify @User email@wisc.edu FullName", color = discord.Color.red()))
        elif isinstance(error, commands.MissingAnyRole):
            await ctx.respond(embed = discord.Embed(title = "Missing required permission", color = discord.Color.red()))
            print(f"non-admin {ctx.message.author} tried to use manualverify")
        else:
            await ctx.respond(embed = discord.Embed(title = "Unknown error. Please contact developers to check logs", color = discord.Color.red()))
            print("Manualverify error: ",error)
###########################################################################
    unverify = SlashCommandGroup("unverify", "Ways to unverify a user or email address")
###########################################################################
    @unverify.command(name = 'user', description = "Removes a user's verification record", debug_guilds=[887366492730036276])
    @commands.has_any_role('Board Member', 'Game Officer', 'Bot Technician', 'Mod', 'Faculty Advisor')
    async def unverifyuser(self, ctx, user: discord.Option(str, "Enter the user to unverify (UserName#0000)", required = True)):

        if('#' not in user):
            return await ctx.respond(embed = discord.Embed(title = "Missing required argument", description = "Please include 4-digit discriminator (#0000)", color = discord.Color.red()))

        await ctx.defer()
        parts = user.split('#', 1)
        name_part = parts[0]
        discriminator_part = parts[1]

        member = discord.utils.get(ctx.guild.members,  name = name_part, discriminator = discriminator_part)
        if member is None:
            return await ctx.respond(embed = discord.Embed(title = "Unknown user", description = f"Could not find {user} in this server", color = discord.Color.red()))


        try:
            cursor, conn = dbconnect()
            #Get the user first, then delete so we can remove role
            cursor.execute("DELETE FROM verified_users WHERE user_id = %s;", (member.id,))
            conn.commit()
            conn.close()

            if (cursor.rowcount != 1): #Did not delete (record not found)
                await ctx.respond(embed = discord.Embed(title = "Record not found", color = discord.Color.red()))
            else: #Deleted
                role = discord.utils.get(ctx.guild.roles, name = "Verified")
                if member != None:
                    if role in member.roles:
                        await member.remove_roles(role)

                await ctx.respond(embed = discord.Embed(title = "Deleted verification record & removed Verified role", color = discord.Color.green()))
        except Exception as error:
            await ctx.respond(embed = discord.Embed(title = "Error:", description = error, color = discord.Color.red()))

    @unverifyuser.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.respond(embed = discord.Embed(title = "Missing required argument", description = "Correct usage: /unverify user UserName#0000", color = discord.Color.red()))
        elif isinstance(error, commands.MissingAnyRole):
            await ctx.respond(embed = discord.Embed(title = "Missing required permission", color = discord.Color.red()))
            print(f"non-admin {ctx.message.author} tried to use unverify user")
        else:
            await ctx.respond(embed = discord.Embed(title = "Unknown error. Please contact developers to check logs", color = discord.Color.red()))
            print("unverify user error: ",error)
###########################################################################
    @unverify.command(name = 'email', description = "Removes any verification record associated with an email", debug_guilds=[887366492730036276])
    @commands.has_any_role('Board Member', 'Game Officer', 'Bot Technician', 'Mod', 'Faculty Advisor')
    async def unverifyemail(self, ctx, email:discord.Option(str, "Enter the wisc email to unverify", required = True)):
        if('@' not in email or'.' not in email):
            return await ctx.respond(embed = discord.Embed(title = "Missing required argument", description = "Please include valid email", color = discord.Color.red()))

        await ctx.defer()

        try:
            cursor, conn = dbconnect()
            #Get the user first, then delete so we can remove role
            cursor.execute("DELETE FROM verified_users WHERE email = %s;", (email,))
            conn.commit()
            conn.close()

            if (cursor.rowcount != 1): #Did not delete (record not found)
                await ctx.respond(embed = discord.Embed(title = "Record not found", color = discord.Color.red()))
            else: #Deleted
                await ctx.respond(embed = discord.Embed(title = "Deleted verification record & removed Verified role", color = discord.Color.green()))
        except Exception as error:
            await ctx.respond(embed = discord.Embed(title = "Error:", description = error, color = discord.Color.red()))

    @unverifyemail.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.respond(embed = discord.Embed(title = "Missing required argument", description = "Correct usage: /unverify email name@wisc.edu", color = discord.Color.red()))
        elif isinstance(error, commands.MissingAnyRole):
            await ctx.respond(embed = discord.Embed(title = "Missing required permission", color = discord.Color.red()))
            print(f"non-admin {ctx.message.author} tried to use unverify email")
        else:
            await ctx.respond(embed = discord.Embed(title = "Unknown error. Please contact developers to check logs", color = discord.Color.red()))
            print("unverify error: ",error)
###########################################################################
def setup(bot):
    bot.add_cog(Verification(bot))
