import discord
from discord.ext import commands
import psycopg2
import datetime
import requests
from asyncio import TimeoutError as asyncioTimeout
from pytz import timezone
import smtplib
import dns.resolver
import socket

from Cogs.db import dbconnect

#verified_table_name = "verified_users"
#verification_attempt_table_name = "verification_requests"

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot=bot
###########################################################################
    @commands.command(name='verify')
    async def verify(self, ctx, email):
        if(discord.utils.get(ctx.author.roles, name = "Verified") != None): # We could have this check the DB, would maybe cause issues with manually verified folks.
            await ctx.send(embed = discord.Embed(title = "You are already verified!", description = "*If you believe this is an error, please message a board member*", color = discord.Color.red()))
            await ctx.message.delete()
            return

        #Check if email has starting/ending parenthesis
        if (email[0] == "("):
            email = email[1:]
        if (email[-1] == ")"):
            email = email[:-1]

        verified, message, color = verify_user(ctx.author.id, email)

        def check(message): #Makes sure user replying equal to user who started the command
            return message.author.id != self.bot.user.id and message.author.id == ctx.author.id

        if verified: #Prompts user to enter name to finish verifying
            author = ctx.message.author
            description = f"{ctx.author}, please enter your first and last name to finish the verification process."
            nameMsg = await ctx.send(embed = discord.Embed(title = message, description = description, color = discord.Color.teal()))

            try:
                response = await self.bot.wait_for("message", check = check, timeout=30)

                message = f"{ctx.author}, you have been successfully verified!"
                await ctx.send(embed = discord.Embed(title = message, color = color))

                insert_verified_user_record(author.id, email, response.content)
                role = discord.utils.get(ctx.guild.roles, name = "Verified")
                await author.add_roles(role)

                await response.delete() #Deletes all messages except final confirmation
                await nameMsg.delete()
                await ctx.message.delete()

            except asyncioTimeout: #asyncio.TimeoutError
                return await ctx.send(embed=discord.Embed(title="Connection timed out! Enter the original command to restart", color = discord.Color.orange()))
        else: #Verification errored, or they have a verification record already in the DB, but lost the role
            await ctx.send(embed = discord.Embed(title = "Error", description = message, color = color))

    @verify.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed = discord.Embed(title = "Missing required argument", description = "Correct usage: !verify **name@wisc.edu** ", color = discord.Color.red()))
###########################################################################
    @commands.command(name = 'whois')
    @commands.has_any_role('Board Member', 'Game Officer', 'Bot Technician', 'Mod', 'Faculty Advisor')
    async def whois(self, ctx, tag):
        if('#' not in tag):
            return await ctx.send(embed = discord.Embed(title = "Missing required argument", description = "Please include 4-digit discriminator (#0000)", color = discord.Color.red()))

        parts = tag.split('#', 1)
        name_part = parts[0]
        discriminator_part = parts[1]

        member = discord.utils.get(ctx.guild.members,  name = name_part, discriminator = discriminator_part)
        if member is None:
            return await ctx.send(embed = discord.Embed(title = "Unkown user", description = f"Could not find {tag} in this server", color = discord.Color.red()))

        email, name, time = get_verification_record(member.id)
        if(email is None):
            return await ctx.send(embed = discord.Embed(title = "Not Verified", description = f"{tag} is not verified.", color = discord.Color.orange()))

        if(name is None):
            name = "*No name registered*"
        time = time.astimezone(timezone("America/Chicago"))
        timestamp = time.strftime("%m/%d/%Y, %I:%M %p %Z")
        recordEmbed = discord.Embed(title = "Verification Record", color = discord.Color.green())
        recordEmbed.add_field(name=("*Name*"),value = name,inline=False)
        recordEmbed.add_field(name=("*Email*"),value = email,inline=False)
        recordEmbed.add_field(name=("*Time Verified*"),value = timestamp,inline=False)
        return await ctx.send(embed = recordEmbed)

    @whois.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed = discord.Embed(title = "Missing required argument", description = "Correct usage: !whois UserName#0000", color = discord.Color.red()))
        elif isinstance(error, commands.MissingAnyRole):
            await ctx.send(embed = discord.Embed(title = "Missing required permission", color = discord.Color.red()))
            print(f"non-admin {ctx.message.author} tried to use whois")
        else:
            await ctx.send(embed = discord.Embed(title = "Unknown error. Please contact developers to check logs", color = discord.Color.red()))
            print("Whois error: ",error)
###########################################################################
    @commands.command(name = "manualverify", aliases = ["manual_verify", "manuallyverify"])
    @commands.has_any_role('Board Member', 'Game Officer', 'Bot Technician', 'Mod', 'Faculty Advisor')
    async def manualverify(self, ctx, user: discord.Member, email, *, full_name):
        if(discord.utils.get(user.roles, name = "Verified") != None):
            await ctx.send(embed = discord.Embed(title = f"{user} is already verified!", color = discord.Color.red()))
            await ctx.message.delete()
            return
        
        verified, message, color = verify_user(user.id, email)
        if verified:
            insert_verified_user_record(user.id, email, full_name)
            role = discord.utils.get(ctx.guild.roles, name = "Verified")
            await user.add_roles(role)

            await ctx.message.delete() #Deletes all messages except final confirmation
            message = f"{user} have been successfully verified!"
            await ctx.send(embed = discord.Embed(title = message, color = color))
        else: #Verification errored
            await ctx.send(embed = discord.Embed(title = "Error", description = message, color = color))

    @manualverify.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed = discord.Embed(title = "Missing required argument", description = "Correct usage: !manualverify @username email@wisc.edu FullName", color = discord.Color.red()))
        elif isinstance(error, commands.MissingAnyRole):
            await ctx.send(embed = discord.Embed(title = "Missing required permission", color = discord.Color.red()))
            print(f"non-admin {ctx.message.author} tried to use manualverify")
        else:
            await ctx.send(embed = discord.Embed(title = "Unknown error. Please contact developers to check logs", color = discord.Color.red()))
            print("Manualverify error: ",error)
###########################################################################
    @commands.command(name = "deleteverification", aliases = ["del_verification", "del_verify", "deleteverify", "delverify"])
    @commands.has_any_role('Board Member', 'Game Officer', 'Bot Technician', 'Mod', 'Faculty Advisor')
    async def del_verify(self, ctx, user: discord.Member):
        try:
            cursor, conn = dbconnect()
            cursor.execute("DELETE FROM verified_users WHERE user_id = %s;", (user.id,))
            conn.commit()
            conn.close()
            
            if (cursor.rowcount != 1): #Did not delete (record not found)
                await ctx.send(embed = discord.Embed(title = "Record not found", color = discord.Color.red()))
            else: #Deleted
                await ctx.send(embed = discord.Embed(title = "Deleted verification record", color = discord.Color.green()))
        except Exception as error:
            await ctx.send(embed = discord.Embed(title = "Error:", description = error, color = discord.Color.red()))    
    
    @del_verify.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed = discord.Embed(title = "Missing required argument", description = "Correct usage: !del_verify @username", color = discord.Color.red()))
        elif isinstance(error, commands.MissingAnyRole):
            await ctx.send(embed = discord.Embed(title = "Missing required permission", color = discord.Color.red()))
            print(f"non-admin {ctx.message.author} tried to use del_verify")
        else:
            await ctx.send(embed = discord.Embed(title = "Unknown error. Please contact developers to check logs", color = discord.Color.red()))
            print("Del_verify error: ",error)
###########################################################################
def insert_verified_user_record(user_id, email, name):
    global time

    cursor, conn = dbconnect()
    time = datetime.datetime.utcnow()

    cursor.execute("INSERT INTO verified_users (user_id, email, time, full_name) VALUES (%s, %s, TIMESTAMP %s, %s);", [user_id, email, time, name])
    if(cursor.rowcount != 1):
        print(f"failed to insert verification record ({user_id}, {email}, {time})")
    conn.commit()
    conn.close()
    return
###########################################################################
def verify_user(user_id, email):
    """
    Attempts to verify the specified user with the specified email address.
    This method does not commit any records to the server!

    Args:
        user_id: The discord userid of the user to be verified
        email: The email address they want to use
    Returns:
        success, message, color: a boolean saying if the user was verified, a message to return to the user, and the color of the returned embed.
                Note that users who are already verified will cause this method to return False.
    """

    if(is_verified(user_id)):
        return False, "You have already been verified, please contact a Board Member or Bot Administrator if you need to receive the role again", discord.Color.red()

    cursor, conn = dbconnect()
    cursor.execute("SELECT user_id FROM verified_users WHERE email = %s;", (email,))
    if(cursor.rowcount > 0):
        print(f"{user_id} Tried to verify with email {email} which is already in use by {cursor.fetchone()[0]}")
        return False, "That email is already in use, talk to a board member if you believe this is an error", discord.Color.red()
    conn.close()

    real, message = verify_email(email)
    if(real):
        return True, f"Your email **{email}** is valid", discord.Color.green()

    if(message == "limit"):
        return False, "Verification daily limit reached, please try again in 24 hours.", discord.Color.red()
    if(message == "Unknown"):
        return False, "Unknown error occurred, please wait a while and try again. Reach out to a board member if this issue persists.", discord.Color.orange()

    return False, f"Sorry, the email address **{email}** is not a valid wisc.edu email address", discord.Color.red()
###########################################################################
def is_verified(user_id):
    """
    Returns whether or not the specified user is already verified
    """
    return get_verified_email(user_id) != None
###########################################################################
def get_verified_email(user_id):
    """
    Returns the verified email associated with the specified user, or None if the user is not verified
    """
    email, name, time = get_verification_record(user_id)
    return email
###########################################################################
def get_verification_record(user_id):
    """
    Returns the verified_user row associated with the specified user_id, or None if the user is not verified
    Returns email, name, timestamp
    """
    cursor, conn = dbconnect()
    cursor.execute("SELECT email, full_name, time FROM verified_users WHERE user_id = %s;", (user_id,))
    if(cursor.rowcount != 1):
        return None, None, None
    row = cursor.fetchone()
    email = row[0]
    name = row[1]
    time = row[2]
    conn.close()
    return email, name, time
###########################################################################
def verify_email(email):
    """
    Attempts to verify an email address.
    """

    #Check that its a wisc.edu ending at least
    if(email.split('@')[-1] != "wisc.edu"):
        return False, "not wisc.edu"

    cursor, conn = dbconnect()
    #Check if this email has been tried recently(one week)
    cursor.execute("SELECT * FROM verification_requests WHERE email = %s AND time > now() - interval '1 week';", (email,))
    if(cursor.rowcount > 0):
        print(f"using Cached request for {email}")
        return cursor.fetchone()[3], "cached"

    #Check that we havnt hit our limit for today
    cursor.execute("SELECT time, daily_request_number FROM verification_requests ORDER BY time DESC LIMIT 1;")
    row = cursor.fetchone()
    number = row[1] + 1
    then = row[0]
    current = datetime.datetime.utcnow()

    if(then.day != current.day or then.month != current.month or then.year != current.year):
        number = 1

    if(number > 99):
        print("HIT DAILY REQUEST LIMIT")
        return False, "limit"

    '''#run request
    response = requests.get("https://isitarealemail.com/api/email/validate",
    params = {'email': email})

    status = response.json()['status']'''

    real = False

    try:
        #get the MX record for wisc.edu
        #Not strictly needed to do this everytime, but it could change and leave us in the lurch so for now its fine
        records = dns.resolver.query('wisc.edu', 'MX')
        mxRecord = str(records[0].exchange)

        #Get local server hostname
        host = socket.gethostname()

        #SMTP lib setup
        server = smtplib.SMTP()
        server.set_debuglevel(0)

        #SMTP Conversation
        code, message = server.connect(mxRecord)
        print(f"connect response: {code} - {message}")

        server.helo(host)
        print(f"HELO response: {server.helo_resp}")

        code, message = server.mail('madisonesportsclub@hotmail.com')
        print(f"mail response: {code} - {message}")

        code, message = server.rcpt(str(email))
        print(f"rcpt response: {code} - {message}")

        server.quit()

        if code == 250: #Valid email
            real = True
    except dns.exception.DNSException as e:
        print(f"DNS Error: {e}")
        return False, "Unknown" # dont want to insert a cache record if it just failed
    except socket.error as e:
        print(f"Failed to connect to SMTP server: {e}")
        return False, "Unknown" # dont want to insert a cache record if it just failed
    except:
        print("******** Uncaught Error **********")
        return False, "Unknown" # dont want to insert a cache record if it just failed

    '''if status == "valid":
        real = True
    elif status == "invalid":
        real = False
    else:
        print(f"email was unknown: {email}, with response: {response}")
        real = True
        #return False, "Unknown"'''

    #save request result
    cursor.execute("INSERT INTO verification_requests(email, time, daily_request_number, result) VALUES (%s, TIMESTAMP %s, %s, %s);", (email, current, number, real))
    if(cursor.rowcount != 1):
        print(f"failed to insert verification request ({email}, {time}, {number}, {real})")
    conn.commit()
    conn.close()
    return real, "from server"
###########################################################################
def insert_name(full_name, user_id):
    print(f"giving user {user_id} the name {full_name}")
    cursor, conn = dbconnect()
    cursor.execute("UPDATE verified_users SET full_name = %s WHERE user_id = %s;", (full_name, user_id))
    if(cursor.rowcount != 1):
        print(f"Failed to give user {user_id} the name {full_name}")
    conn.commit()
    conn.close()
###########################################################################
def setup(bot):
    bot.add_cog(Verification(bot))
