import discord
import smtplib
import dns.resolver
import socket
import datetime

from Cogs.db import dbconnect
from Cogs.Helpers.websiteHelpers import add_email

###########################################################################
# Prevents non-text channel from being used since SlashCommandOptionType.textChannel doesn't exist
def checkTextChannel(channel):
    return type(channel) == discord.channel.TextChannel
###########################################################################
async def insert_verified_user_record(user_id, email, name):
    global time

    cursor, conn = dbconnect()
    time = datetime.datetime.utcnow()

    cursor.execute("INSERT INTO verified_users (user_id, email, time, full_name) VALUES (%s, %s, TIMESTAMP %s, %s);", [user_id, email, time, name])
    if(cursor.rowcount != 1):
        print(f"failed to insert verification record ({user_id}, {email}, {time})")
    else:
        await add_email(email)

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

    real = False

    try:
        print("pinging UW")
        #get the MX record for wisc.edu
        #Not strictly needed to do this everytime, but it could change and leave us in the lurch so for now its fine
        records = dns.resolver.resolve('wisc.edu', 'MX')
        lowpref = records[0].preference
        mxRecord = str(records[0].exchange)
        for record in records:
            if record.preference < lowpref:
                lowpref = record.preference
                mxRecord = str(record.exchange)

        print("Got record: " + mxRecord)

        #Get local server hostname
        host = socket.gethostname()

        #SMTP lib setup
        server = smtplib.SMTP(timeout = 2)
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
        return True, "Unknown" # dont want to insert a cache record if it just failed
    except socket.error as e:
        print(f"Failed to connect to SMTP server: {e}")
        return True, "Unknown" # dont want to insert a cache record if it just failed
    except:
        print("******** Uncaught Error **********")
        return True, "Unknown" # dont want to insert a cache record if it just failed

    #save request result
    cursor.execute("INSERT INTO verification_requests(email, time, daily_request_number, result) VALUES (%s, TIMESTAMP %s, %s, %s);", (email, current, number, real))
    if(cursor.rowcount != 1):
        print(f"failed to insert verification request ({email}, {current}, {number}, {real})")
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
