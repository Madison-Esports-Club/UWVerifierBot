#Cog for verifying
from asyncio.windows_events import NULL
import discord
from discord.ext import commands
import psycopg2
import datetime
import requests
from asyncio import TimeoutError as asyncioTimeout

from Cogs.db import dbconnect

#verified_table_name = "verified_users"
#verification_attempt_table_name = "verification_requests"

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot=bot
###########################################################################
    @commands.command(name='verify')
    async def verify(self, ctx, email):
        if(discord.utils.get(ctx.author.roles, name = "Verified") != None):
            await ctx.send(embed = discord.Embed(title = "you are already verified!", description = "*If you believe this is an error, please message a board member*", color = discord.Color.red()))
            return
        #print(ctx.author.id)
        verified, message, color = self.verify_user(ctx.author.id, email)
        response = "Thank you for submitting your verification request, it will be processed within 24 hours."
        
        def check(user): #Makes sure user replying equal to user who started the command
            return user != self.bot.user and author == ctx.author

        if verified: #Prompts user to enter name to finish verifying
            author = ctx.message.author
            description = "Please enter your first and last name to finish the process"
            await ctx.send(embed = discord.Embed(title = message, description = description, color = discord.Color.teal()))
            
            try:
                response = await self.bot.wait_for("message", check = check, timeout=30)
                
                #response == name
                #Insert name into database here
                
                message = "You have been successfully verified!"
                await ctx.send(embed = discord.Embed(title = message, color = color))

            except asyncioTimeout: #asyncio.TimeoutError
                return await ctx.send(embed=discord.Embed(title="Connection timed out! Enter the original command to restart", color = discord.Color.orange()))
        else: #Verification errored
            await ctx.send(embed = discord.Embed(title = "Error", description = message, color = color))
 
    @verify.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed = discord.Embed(title = "Missing required permission", description = "Correct usage: !verify **name@wisc.edu** ", color= discord.Color.red()))
    
    '''
    Example cog function: 
    @commands.command(name="unlock") #The name is what the command used by the user is. You can also do name="unlock", aliases=["un-lock", "unlock1"]) etc to have multiple ways to use the command (always have to be in dict form)
    @commands.has_permissions(manage_channels=True) #Optional check for permissions
    async def unlock(self, ctx): #self and ctx always required for cogs (main difference)
        perms=ctx.channel.overwrites_for(ctx.guild.default_role)
        perms.send_messages=True
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=perms)
        await ctx.send(embed=discord.Embed(title=f"**{ctx.channel}** unlocked to non-admin users"))
        
    @unlock.error #Error handling
    async def clear_error(self, ctx, error):
        if isinstance(error,commands.MissingPermissions):
            await ctx.send(embed=discord.Embed(title="You don't have perms to do that dummy (Requires `Manage Channels` permission)"))
    '''

###########################################################################
    def verify_user(self, user_id, email):
        """
        Attempts to verify the specified user with the specified email address

        Args:
            user_id: The discord userid of the user to be verified
            email: The email address they want to use
        Returns:
            success, message, color: a boolean saying if the user was verified, a message to return to the user, and the color of the returned embed.
                    Note that users who are already verified will cause this method to return False.
        """
        if(self.is_verified(user_id)):
            return False, "You're already verified!", discord.Color.red()

        #Check that its a wisc.edu ending at least
        if(email.split('@')[-1] != "wisc.edu"):
            return False, f"**{email}** is not a wisc.edu email address.", discord.Color.red()

        cursor, conn = dbconnect()
        cursor.execute("SELECT user_id FROM verified_users WHERE email = %s;", (email,))
        if(cursor.rowcount > 0):
            print(f"{user_id} Tried to verify with email {email} which is already in use by {cursor.fetchone()[0]}")
            return False, "That email is already in use, talk to a board member if you believe this is an error", discord.Color.red()

        real, message = self.verify_email(email)
        if(real):
            cursor.execute("INSERT INTO verified_users (user_id, email, time) VALUES (%s, %s, TIMESTAMP %s);", [user_id, email, datetime.datetime.utcnow()])
            conn.commit()
            conn.close()
            return True, f"Congratulations, you are now verified with the email **{email}**!", discord.Color.green()
            if(message == "limit"):
                conn.close()
                return False, "Verification daily limit reached, please try again in 24 hours.", discord.Color.red()
        if(message == "Unknown"):
            conn.close()
            return False, "Unknown error occurred, please wait a while and try again. Reach out to a board member if this issue persists.", discord.Color.orange()

        conn.close()
        return False, f"Sorry, the email address **{email}** is not a valid wisc.edu email address", discord.Color.red()
###########################################################################
    def is_verified(self, user_id):
        """
        Returns whether or not the specified user is already verified
        """
        return self.get_verified_email(user_id) != None
###########################################################################
    def get_verified_email(self, user_id):
        """
        Returns the verified email associated with the specified user, or None if the user is not verified
        """
        cursor, conn = dbconnect()
        cursor.execute("SELECT email FROM verified_users WHERE user_id = %s;", (user_id,))
        if(cursor.rowcount != 1):
            return None
        email = cursor.fetchone()[0]
        conn.close()
        return email
###########################################################################
    def verify_email(self, email):
        """
        Attempts to verify an email address.
        """
        cursor, conn = dbconnect()
        #Check if this email has been tried recently(one week)
        # cursor.execute("SELECT * FROM verification_requests WHERE email = %s AND time > now() - interval '1 week';", (email,))
        if(cursor.rowcount > 0):
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

        #run request
        response = requests.get("https://isitarealemail.com/api/email/validate",
        params = {'email': email})

        status = response.json()['status']
        real = False
        if status == "valid":
            real = True
        elif status == "invalid":
            real = False
        else:
            print(f"email was unknown: {email}, with response: {response}")
            return False, "Unknown"

        #save request result
        cursor.execute("INSERT INTO verification_requests(email, time, daily_request_number, result) VALUES (%s, TIMESTAMP %s, %s, %s);", (email, current, number, real))
        conn.commit()
        conn.close()
        return real, "from server"
###########################################################################
def setup(bot):
    bot.add_cog(Verification(bot))
