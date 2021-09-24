#Cog for verifying
import discord
from discord.ext import commands

from Cogs.db import dbconnect

class Verification(commands.Cog):
    def __init__(self,bot):
        self.bot=bot
###########################################################################
#Commands in cogs have different syntax than commands that arent in a cog. Example: (pasted from my own code just delete when you're done with this)

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
###########################################################################
def setup(bot):
    bot.add_cog(Verification(bot))
