import discord
from discord.ext import commands

from Cogs.Helpers.helpers import checkTextChannel
from Cogs.db import dbconnect

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
###########################################################################
    @discord.slash_command(name = "setwelcomechannel", debug_guilds=[887366492730036276]) #Sets the channel that member-join messages are sent
    @commands.has_permissions(manage_guild = True)
    async def setwelcomechannel(self, ctx, channel: discord.Option(discord.SlashCommandOptionType.channel, "Select channel")):
        if (not checkTextChannel(channel)):
            return await ctx.respond(embed = discord.Embed(title = "Channel selected must be a text channel", color = discord.Color.red()))
        
        cursor,conn = dbconnect() #Opens connection to db
        channel = channel.id
        try:
            sql = ("SELECT * FROM guild_settings WHERE (guild_id = %s AND setting = %s)")
            cursor.execute(sql, (ctx.guild.id, "welcome_channel"))
            if cursor.fetchone() is not None:
                sql = ('''UPDATE guild_settings
                        SET setting_value = %s
                        WHERE (guild_id = %s AND setting = %s)''')
                cursor.execute(sql, (channel, ctx.guild.id, "welcome_channel"))
                conn.commit()
            else:
                sql = ('''INSERT INTO guild_settings(guild_id, setting, setting_value)
                    VALUES (%s, %s, %s)''')
                cursor.execute(sql, (ctx.guild.id, "welcome_channel", channel))
                conn.commit()
        except Exception as e:
            print (e)
        await ctx.respond(embed = discord.Embed(title = "Join channel set!", color = discord.Color.green()))
        conn.close() #Closes connection to db


    @setwelcomechannel.error
    async def clear_error(self, ctx, error):
        if isinstance(error,commands.BadArgument):
            await ctx.respond(embed = discord.Embed(title = "Text channel not found!", color = discord.Color.red()))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.respond(embed = discord.Embed(title = "Enter the text channel you want to set it to!\n`/setwelcomechannel (channel)`", color = discord.Color.red()))
        elif isinstance(error, commands.MissingPermissions):
            await ctx.respond(embed = discord.Embed(title = "Missing `Manage Server` permission", color = discord.Color.red()))
###########################################################################
    @discord.slash_command(name = "setleavechannel", debug_guilds=[887366492730036276]) #Sets the channel that member-leave messages are sent
    @commands.has_permissions(manage_guild = True)
    async def setleavechannel(self, ctx, channel: discord.Option(discord.SlashCommandOptionType.channel, "Select channel")):
        if (not checkTextChannel(channel)):
            return await ctx.respond(embed = discord.Embed(title = "Channel selected must be a text channel", color = discord.Color.red()))
        
        cursor,conn = dbconnect() #Opens connection to db
        channel = channel.id
        try:
            sql = ("SELECT * FROM guild_settings WHERE (guild_id = %s AND setting = %s)")
            cursor.execute(sql, (ctx.guild.id, "leave_channel"))
            if cursor.fetchone() is not None:
                sql = ('''UPDATE guild_settings
                        SET setting_value = %s
                        WHERE (guild_id = %s AND setting = %s)''')
                cursor.execute(sql, (channel, ctx.guild.id, "leave_channel"))
                conn.commit()
            else:
                sql = ('''INSERT INTO guild_settings(guild_id, setting, setting_value)
                    VALUES (%s, %s, %s)''')
                cursor.execute(sql, (ctx.guild.id, "leave_channel", channel))
                conn.commit()
        except Exception as e:
            print (e)
        await ctx.respond(embed = discord.Embed(title = "Leave channel set!",color = discord.Color.green()))
        conn.close() #Closes connection to db
            
    @setleavechannel.error
    async def clear_error(self, ctx, error):
        if isinstance(error,commands.BadArgument):
            await ctx.respond(embed = discord.Embed(title = "Text channel not found!",color = discord.Color.red()))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.respond(embed = discord.Embed(title = "Enter the text channel you want to set it to!\n`/setleavechannel (channel)`",color = discord.Color.red()))
        elif isinstance(error, commands.MissingPermissions):
            await ctx.respond(embed = discord.Embed(title = "Missing `Manage Server` permission",color = discord.Color.red()))
###########################################################################
    @discord.slash_command(name = "setleavemsg", debug_guilds=[887366492730036276]) #Sets member-leave message
    @commands.has_permissions(manage_guild = True)
    async def setleavemsg(self, ctx, *, message: discord.Option(discord.SlashCommandOptionType.string, "Enter leave message", required = False)):
        cursor,conn = dbconnect() #Opens connection to db
        if message is None:
            message = ("Adios **%s**...")

        try:
            sql = ("SELECT * FROM guild_settings WHERE (guild_id = %s AND setting = %s)")
            cursor.execute(sql, (ctx.guild.id,"leave_msg"))
            if cursor.fetchone() is not None:
                sql = ('''UPDATE guild_settings
                    SET setting_value = %s
                    WHERE (guild_id = %s AND setting = %s)''')
                cursor.execute(sql, (message, ctx.guild.id, "leave_msg"))
                conn.commit()
            else:
                sql = ('''INSERT INTO guild_settings(guild_id, setting, setting_value)
                    VALUES (%s, %s, %s)''')
                cursor.execute(sql, (ctx.guild.id, "leave_msg",message))
                conn.commit()
            embed = discord.Embed(title = "Leave message set!",color = discord.Color.green())
            embed.add_field(name = "Test message:",value = message%ctx.author.mention)
            await ctx.respond(embed = embed)
        except Exception as e:
            print (e)
        conn.close() #Closes connection to db
        
    @setleavemsg.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond(embed = discord.Embed(title = "Missing `Manage Server` permission"))
###########################################################################
    @discord.slash_command(name = "enableleavemsg", debug_guilds=[887366492730036276]) #Enables/disables member-leave message
    @commands.has_permissions(manage_guild = True)
    async def enableleavemsg(self, ctx, status: discord.Option(discord.SlashCommandOptionType.boolean, "Enable/disable leave message", required = True)):
        cursor,conn = dbconnect() #Opens connection to db
        if (status):
            status = "True"
            title = "Leave message enabled"
        else:
            status = "False"
            title = "Leave message disabled"
        sql = ("SELECT * FROM guild_settings WHERE (guild_id = %s AND setting = %s)")
        cursor.execute(sql, (ctx.guild.id,"leave_status"))
        if cursor.fetchone() is not None:
            sql = ('''UPDATE guild_settings
                SET setting_value = %s
                WHERE (guild_id = %s AND setting = %s)''')
            cursor.execute(sql, (status, ctx.guild.id, "leave_status"))
            conn.commit()
        else:
            sql = ('''INSERT INTO guild_settings(guild_id, setting, setting_value)
                 VALUES (%s, %s, %s)''')
            cursor.execute(sql, (ctx.guild.id, "leavestatus",status))
            conn.commit()
        await ctx.respond(embed = discord.Embed(title = title,color = discord.Color.dark_teal()))
        conn.close() #Closes connection to db

    @enableleavemsg.error
    async def clear_error(self, ctx, error):
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.respond(embed = discord.Embed(title = "Missing required argument\nProper usage: `!enableleavemsg (true/false)`"))
        elif isinstance(error, commands.MissingPermissions):
            await ctx.respond(embed = discord.Embed(title = "Missing `Manage Server` permission"))
###########################################################################
    @discord.slash_command(name = "leavepicture", debug_guilds=[887366492730036276]) #Sets the gif that gets sent when a member leaves
    @commands.has_permissions(manage_guild = True)
    async def leavepicture(self, ctx, picture: discord.Option(discord.SlashCommandOptionType.string, "Enter url for picture, leave blank for default picture", required = False)):
        cursor,conn = dbconnect() #Opens connection to db
        if picture is None:
            sql = ("SELECT * FROM guild_settings WHERE (guild_id = %s AND setting = %s)")
            cursor.execute(sql, (ctx.guild.id,"leave_picture"))
            if cursor.fetchone() is not None:
                sql = ('''UPDATE guild_settings
                    SET setting_value = %s
                    WHERE (guild_id = %s AND setting = %s)''')
                cursor.execute(sql, ("https://media.giphy.com/media/26u4b45b8KlgAB7iM/giphy.gif?cid=790b7611485e4b17dd30b01e42eae6ed2568acb8d39c1e23&rid=giphy.gif&ct=g", ctx.guild.id, "leave_picture"))
                conn.commit()
            else:
                sql = ('''INSERT INTO guild_settings(guild_id, setting, setting_value)
                    VALUES (%s, %s, %s)''')
                cursor.execute(sql, (ctx.guild.id, "leave_picture","https://media.giphy.com/media/26u4b45b8KlgAB7iM/giphy.gif?cid=790b7611485e4b17dd30b01e42eae6ed2568acb8d39c1e23&rid=giphy.gif&ct=g"))
                conn.commit()
            return await ctx.respond(embed = discord.Embed(title = "Picture reset to default image"))

        embed = discord.Embed(title = "Test Image: Is this the correct image? React with the proper emoji")
        embed.set_image(url = picture)
        msg = await ctx.respond(embed = embed)

        def check(reaction,user):
            return user !=  self.bot.user and user  ==  ctx.author and (str(reaction.emoji) in reactEmojis)

        reactEmojis = ["✔️","❌"]
        for emoji in reactEmojis:
            await msg.add_reaction(emoji)
        
        response,_ = await self.bot.wait_for("reaction_add",check = check, timeout = 30)
        if response.emoji == "✔️":
            sql = ("SELECT * FROM guild_settings WHERE (guild_id = %s AND setting = %s)")
            cursor.execute(sql, (ctx.guild.id,"leave_picture"))
            if cursor.fetchone() is not None:
                sql = ('''UPDATE guild_settings
                    SET setting_value = %s
                    WHERE (guild_id = %s AND setting = %s)''')
                cursor.execute(sql, (picture, ctx.guild.id, "leave_picture"))
            else:
                sql = ('''INSERT INTO guild_settings(guild_id, setting, setting_value)
                    VALUES (%s, %s, %s)''')
                cursor.execute(sql, (ctx.guild.id, "leave_picture",picture))
            conn.commit()
            await ctx.respond(embed = discord.Embed(title = "Leave picture set! :slight_smile:"))
        else:
            await ctx.respond(embed = discord.Embed(title = "Restart the command and try to paste a different link!"))
        conn.close() #Closes connection to db

    @leavepicture.error
    async def clear_error(self, ctx, error):
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.respond(embed = discord.Embed(title = "Missing required argument. Use 'default' as the url to revert to original picture\nProper usage: `!leavepicture (image link)`",color = discord.Color.red()))
        elif isinstance(error, commands.MissingPermissions):
            await ctx.respond(embed = discord.Embed(title = "Missing `Manage Server` permission"))
###########################################################################
    @discord.slash_command(name = "setwelcomemsg", debug_guilds=[887366492730036276]) #Sets welcome message
    @commands.has_permissions(manage_guild = True)
    async def setwelcomemsg(self, ctx, *, message: discord.Option(discord.SlashCommandOptionType.string, "Enter join message", required = False)):
        cursor,conn = dbconnect() #Opens connection to db
        if message is None:
            message = ("Welcome %s to the server!")
        
        try:
            sql = ("SELECT * FROM guild_settings WHERE (guild_id = %s AND setting = %s)")
            cursor.execute(sql, (ctx.guild.id,"welcome_msg"))
            if cursor.fetchone() is not None:
                sql = ('''UPDATE guild_settings
                    SET setting_value = %s
                    WHERE (guild_id = %s AND setting = %s)''')
                cursor.execute(sql, (message, ctx.guild.id, "welcome_msg"))
                conn.commit()
            else:
                sql = ('''INSERT INTO guild_settings(guild_id, setting, setting_value)
                    VALUES (%s, %s, %s)''')
                cursor.execute(sql, (ctx.guild.id, "welcome_msg",message))
                conn.commit()
            embed = discord.Embed(title = "Welcome message set!",color = discord.Color.green())
            embed.add_field(name = "Test message:",value = message%ctx.author.mention)
            await ctx.respond(embed = embed)
        except Exception as e:
            print (e)
        conn.close() #Closes connection to db
    
    @setwelcomemsg.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond(embed = discord.Embed(title = "Missing `Manage Server` permission"))
###########################################################################
    @discord.slash_command(name = "enablewelcomemsg", debug_guilds=[887366492730036276]) #Enables/disables welcome message
    @commands.has_permissions(manage_guild = True)
    async def enablewelcomemsg(self, ctx, status: discord.Option(discord.SlashCommandOptionType.boolean, "Enable/disable join message", required = True)):
        
        cursor,conn = dbconnect() #Opens connection to db

        if (status):
            status = "True"
            title = "Welcome message enabled"
        else:
            status = "False"
            title = "Welcome message disabled"
        sql = ("SELECT * FROM guild_settings WHERE (guild_id = %s AND setting = %s)")
        cursor.execute(sql, (ctx.guild.id,"welcome_status"))
        if cursor.fetchone() is not None:
            sql = ('''UPDATE guild_settings
                SET setting_value = %s
                WHERE (guild_id = %s AND setting = %s)''')
            cursor.execute(sql, (status, ctx.guild.id, "welcome_status"))
            conn.commit()
        else:
            sql = ('''INSERT INTO guild_settings(guild_id, setting, setting_value)
                 VALUES (%s, %s, %s)''')
            cursor.execute(sql, (ctx.guild.id, "welcome_status",status))
            conn.commit()
        await ctx.respond(embed = discord.Embed(title = title,color = discord.Color.dark_teal()))
        conn.close() #Closes connection to db

    @enablewelcomemsg.error
    async def clear_error(self, ctx, error):
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.respond(embed = discord.Embed(title = "Missing required argument\nProper usage: `!enablewelcomemsg (true/false)`"))
        elif isinstance(error, commands.MissingPermissions):
            await ctx.respond(embed = discord.Embed(title = "Missing `Manage Server` permission"))
###########################################################################
    @discord.slash_command(name = "welcomepicture", debug_guilds=[887366492730036276]) #Sets welcome gif
    @commands.has_permissions(manage_guild = True)
    async def welcomepicture(self, ctx, picture: discord.Option(discord.SlashCommandOptionType.string, "Enter url for picture, leave blank for default picture", required = False)):
        cursor,conn = dbconnect() #Opens connection to db
        if picture is None:
            sql = ("SELECT * FROM guild_settings WHERE (guild_id = %s AND setting = %s)")
            cursor.execute(sql, (ctx.guild.id,"welcome_picture"))
            if cursor.fetchone() is not None:
                sql = ('''UPDATE guild_settings
                    SET setting_value = %s
                    WHERE (guild_id = %s AND setting = %s)''')
                cursor.execute(sql, ("https://media.tenor.co/images/3ccff8c4b2443d93811eac9b2fd56f11/raw", ctx.guild.id, "welcome_picture"))
                conn.commit()
            else:
                sql = ('''INSERT INTO guild_settings(guild_id, setting, setting_value)
                    VALUES (%s, %s, %s)''')
                cursor.execute(sql, (ctx.guild.id, "welcome_picture","https://media.tenor.co/images/3ccff8c4b2443d93811eac9b2fd56f11/raw"))
                conn.commit()
            return await ctx.respond(embed = discord.Embed(title = "Picture reset to default image"))

        embed = discord.Embed(title = "Test Image: Is this the correct image? React with the proper emoji")
        embed.set_image(url = picture)
        msg = await ctx.respond(embed = embed)

        def check(reaction,user):
            return user !=  self.bot.user and user  ==  ctx.author and (str(reaction.emoji) in reactEmojis)

        reactEmojis = ["✔️","❌"]
        for emoji in reactEmojis:
            await msg.add_reaction(emoji)
        
        response,_ = await self.bot.wait_for("reaction_add",check = check, timeout = 30)
        if response.emoji == "✔️":
            sql = ("SELECT * FROM guild_settings WHERE (guild_id = %s AND setting = %s)")
            cursor.execute(sql, (ctx.guild.id,"welcome_picture"))
            if cursor.fetchone() is not None:
                sql = ('''UPDATE guild_settings
                    SET setting_value = %s
                    WHERE (guild_id = %s AND setting = %s)''')
                cursor.execute(sql, (picture, ctx.guild.id, "welcome_picture"))
            else:
                sql = ('''INSERT INTO guild_settings(guild_id, setting, setting_value)
                    VALUES (%s, %s, %s)''')
                cursor.execute(sql, (ctx.guild.id, "welcome_picture",picture))
            conn.commit()
            await ctx.respond(embed = discord.Embed(title = "Welcome picture set! :slight_smile:"))
        else:
            await ctx.respond(embed = discord.Embed(title = "Restart the command and try to paste a different link!"))
        conn.close() #Closes connection to db

    @welcomepicture.error
    async def clear_error(self, ctx, error):
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.respond(embed = discord.Embed(title = "Missing required argument. Use 'default' as the url to revert to original picture\nProper usage: `!welcomepicture (image link)`",color = discord.Color.red()))
        elif isinstance(error, commands.MissingPermissions):
            await ctx.respond(embed = discord.Embed(title = "Missing `Manage Server` permission"))
###########################################################################
def setup(bot):
    bot.add_cog(Settings(bot))