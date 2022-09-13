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
    async def verify(self, ctx, email, fullname):
        if(discord.utils.get(ctx.author.roles, name = "Verified") != None): # We could have this check the DB, would maybe cause issues with manually verified folks.
            await ctx.respond(embed = discord.Embed(title = "You are already verified!", description = "*If you believe this is an error, please message a board member*", color = discord.Color.red()))
            return

        await ctx.defer()

        #Trims parameters
        email = email.strip()
        fullname = fullname.strip()

        verified, message, color = verify_user(ctx.author.id, email)

        if verified: #Prompts user to enter name to finish verifying

            insert_verified_user_record(ctx.author.id, email, fullname)
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
    async def whois(self, ctx, user):
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
    async def manualverify(self, ctx, member: discord.Option(discord.SlashCommandOptionType.user), email: discord.Option(discord.SlashCommandOptionType.string), full_name: discord.Option(discord.SlashCommandOptionType.string)):
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
    async def unverifyuser(self, ctx, user:discord.Option(str)):

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
    async def unverifyemail(self, ctx, email:discord.Option(str)):

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
# ###########################################################################
# def insert_verified_user_record(user_id, email, name):
#     global time

#     cursor, conn = dbconnect()
#     time = datetime.datetime.utcnow()

#     cursor.execute("INSERT INTO verified_users (user_id, email, time, full_name) VALUES (%s, %s, TIMESTAMP %s, %s);", [user_id, email, time, name])
#     if(cursor.rowcount != 1):
#         print(f"failed to insert verification record ({user_id}, {email}, {time})")
#     conn.commit()
#     conn.close()
#     return
# ###########################################################################
# def verify_user(user_id, email):
#     """
#     Attempts to verify the specified user with the specified email address.
#     This method does not commit any records to the server!

#     Args:
#         user_id: The discord userid of the user to be verified
#         email: The email address they want to use
#     Returns:
#         success, message, color: a boolean saying if the user was verified, a message to return to the user, and the color of the returned embed.
#                 Note that users who are already verified will cause this method to return False.
#     """

#     if(is_verified(user_id)):
#         return False, "You have already been verified, please contact a Board Member or Bot Administrator if you need to receive the role again", discord.Color.red()

#     cursor, conn = dbconnect()
#     cursor.execute("SELECT user_id FROM verified_users WHERE email = %s;", (email,))
#     if(cursor.rowcount > 0):
#         print(f"{user_id} Tried to verify with email {email} which is already in use by {cursor.fetchone()[0]}")
#         return False, "That email is already in use, talk to a board member if you believe this is an error", discord.Color.red()
#     conn.close()

#     real, message = verify_email(email)
#     if(real):
#         return True, f"Your email **{email}** is valid", discord.Color.green()

#     if(message == "limit"):
#         return False, "Verification daily limit reached, please try again in 24 hours.", discord.Color.red()
#     if(message == "Unknown"):
#         return False, "Unknown error occurred, please wait a while and try again. Reach out to a board member if this issue persists.", discord.Color.orange()

#     return False, f"Sorry, the email address **{email}** is not a valid wisc.edu email address", discord.Color.red()
# ###########################################################################
# def is_verified(user_id):
#     """
#     Returns whether or not the specified user is already verified
#     """
#     return get_verified_email(user_id) != None
# ###########################################################################
# def get_verified_email(user_id):
#     """
#     Returns the verified email associated with the specified user, or None if the user is not verified
#     """
#     email, name, time = get_verification_record(user_id)
#     return email
# ###########################################################################
# def get_verification_record(user_id):
#     """
#     Returns the verified_user row associated with the specified user_id, or None if the user is not verified
#     Returns email, name, timestamp
#     """
#     cursor, conn = dbconnect()
#     cursor.execute("SELECT email, full_name, time FROM verified_users WHERE user_id = %s;", (user_id,))
#     if(cursor.rowcount != 1):
#         return None, None, None
#     row = cursor.fetchone()
#     email = row[0]
#     name = row[1]
#     time = row[2]
#     conn.close()
#     return email, name, time
# ###########################################################################
# def verify_email(email):
#     """
#     Attempts to verify an email address.
#     """

#     #Check that its a wisc.edu ending at least
#     if(email.split('@')[-1] != "wisc.edu"):
#         return False, "not wisc.edu"

#     cursor, conn = dbconnect()
#     #Check if this email has been tried recently(one week)
#     cursor.execute("SELECT * FROM verification_requests WHERE email = %s AND time > now() - interval '1 week';", (email,))
#     if(cursor.rowcount > 0):
#         print(f"using Cached request for {email}")
#         return cursor.fetchone()[3], "cached"

#     #Check that we havnt hit our limit for today
#     cursor.execute("SELECT time, daily_request_number FROM verification_requests ORDER BY time DESC LIMIT 1;")
#     row = cursor.fetchone()
#     number = row[1] + 1
#     then = row[0]
#     current = datetime.datetime.utcnow()

#     if(then.day != current.day or then.month != current.month or then.year != current.year):
#         number = 1

#     if(number > 99):
#         print("HIT DAILY REQUEST LIMIT")
#         return False, "limit"

#     real = False

#     try:
#         print("pinging UW")
#         #get the MX record for wisc.edu
#         #Not strictly needed to do this everytime, but it could change and leave us in the lurch so for now its fine
#         records = dns.resolver.resolve('wisc.edu', 'MX')
#         lowpref = records[0].preference
#         mxRecord = str(records[0].exchange)
#         for record in records:
#             if record.preference < lowpref:
#                 lowpref = record.preference
#                 mxRecord = str(record.exchange)

#         print("Got record: " + mxRecord)

#         #Get local server hostname
#         host = socket.gethostname()

#         #SMTP lib setup
#         server = smtplib.SMTP(timeout = 2)
#         server.set_debuglevel(0)

#         #SMTP Conversation
#         code, message = server.connect(mxRecord)
#         print(f"connect response: {code} - {message}")

#         server.helo(host)
#         print(f"HELO response: {server.helo_resp}")

#         code, message = server.mail('madisonesportsclub@hotmail.com')
#         print(f"mail response: {code} - {message}")

#         code, message = server.rcpt(str(email))
#         print(f"rcpt response: {code} - {message}")

#         server.quit()

#         if code == 250: #Valid email
#             real = True
#     except dns.exception.DNSException as e:
#         print(f"DNS Error: {e}")
#         return True, "Unknown" # dont want to insert a cache record if it just failed
#     except socket.error as e:
#         print(f"Failed to connect to SMTP server: {e}")
#         return True, "Unknown" # dont want to insert a cache record if it just failed
#     except:
#         print("******** Uncaught Error **********")
#         return True, "Unknown" # dont want to insert a cache record if it just failed

#     #save request result
#     cursor.execute("INSERT INTO verification_requests(email, time, daily_request_number, result) VALUES (%s, TIMESTAMP %s, %s, %s);", (email, current, number, real))
#     if(cursor.rowcount != 1):
#         print(f"failed to insert verification request ({email}, {current}, {number}, {real})")
#     conn.commit()
#     conn.close()
#     return real, "from server"
# ###########################################################################
# def insert_name(full_name, user_id):
#     print(f"giving user {user_id} the name {full_name}")
#     cursor, conn = dbconnect()
#     cursor.execute("UPDATE verified_users SET full_name = %s WHERE user_id = %s;", (full_name, user_id))
#     if(cursor.rowcount != 1):
#         print(f"Failed to give user {user_id} the name {full_name}")
#     conn.commit()
#     conn.close()
# ###########################################################################
def setup(bot):
    bot.add_cog(Verification(bot))
