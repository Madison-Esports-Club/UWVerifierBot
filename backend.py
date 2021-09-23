"""These are the three functions I will implement. user_id should be the one returned from discord.py, not their tag and number

#returns (success, message)
def verify_user(user_id, email):

#returns true or false
def is_verified(user_id):

#returns either the email that the specified user is verified with, or None
def get_verified_email(user_id):"""

import os
import psycopg2

DATABASE_URL = os.environ['DATABASE_URL']

conn = psycopg2.connect(DATABASE_URL, sslmode='require')

cursor = conn.cursor()
cursor.execute("SET TIME ZONE 'America/Chicago'")

def verify_backlog():
	cursor.execute("SELECT * from to_verify;")
	numrows = cursor.rowcount
	rowdata = cursor.fetchall()

	for(row in rowdata):
		real = verify_email(row[2])
		if(real):
			bot.send_response(row[0], row[1], row[2], true, "email verified")
			log_verification(row[0], row[1], row[2])
		else:
			bot.send_response(row[0], row[1], row[2], false, "email not verified")

def log_verification(user_id, guild_id, email):
	cursor.execute("INSERT INTO verified (user_id, guild_id, email) VALUES (%s, %s, %s, %dt);", (user_id, guild_id, email, datetime.datetime.now()))
	if(rowcount != 1):
		print("Failed to log verified email " + email + " for user " + user_id)

def
