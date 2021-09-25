import asyncio
import psycopg2
import os
from configparser import ConfigParser
import discord
from discord.ext import commands

class db(commands.Cog):
    def __init__(self,bot):
        self.bot=bot
###########################################################################
def dbconnect():               #When calling from a function in another file use: cursor,conn=dbconnect()
    try: #Trys to connect from Heroku
        conn=psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")
        cursor = conn.cursor()
    except: #Connects from system files instead
        config_object=ConfigParser()
        config_object.read("BotVariables.ini")
        variables=config_object["variables"]
        DATABASE_URL=variables["DATABASE_URL"]
        conn = psycopg2.connect(DATABASE_URL, sslmode='prefer')
        cursor = conn.cursor()
    return cursor, conn
###########################################################################
def setup(bot):
    bot.add_cog(db(bot))
