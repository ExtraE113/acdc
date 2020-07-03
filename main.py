import discord
from tinydb import TinyDB, where, Query
from tinydb.operations import increment
import datetime


client = discord.Client()
db = TinyDB("db.json")
config = TinyDB("config.json")
config_data = config.table("config")
users = db.table("users")
pending = db.table("pending")

STAFF_ID = config_data.all()[0]["STAFF_ID"]
TOKEN = config_data.all()[0]["TOKEN"]

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    print(f"PENDING ALL: {pending.all()}")
    print(f"USERS ALL: {users.all()}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!rankup'):
        author_id = str(message.author.id)
        query = Query()
        user = users.search(query.name == author_id)
        if (len(user) == 0):
            users.insert({"name" : author_id, "rank" : 1})
            user = users.search(query.name == author_id)

        rank = user[-1]['rank']

        msg = f"{message.author.mention} requested a rank up. They are currently rank {rank}, and have been in the Discord for {datetime.datetime.utcnow() - message.author.joined_at}. <@&{STAFF_ID}> use emoticons to either grant or deny the rank up request."
        print(msg)
        outbound = await  message.channel.send(msg)

        print(f"OUTBOUND ID: {outbound.id}")

        pending.insert({"message_id" : outbound.id, "user" : author_id})

        await outbound.add_reaction("👍")
        await outbound.add_reaction("👎")

    elif message.content.startswith("!rank?"):
        mentions = message.mentions

        if len(mentions) == 0:
            mentions = [message.author]

        msg = ""

        for i in mentions:
            query = Query()
            user = users.search(query.name == i.id)
            if (len(user) == 0):
                users.insert({"name": i.id, "rank": 1})
                user = users.search(query.name == i.id)

            rank = user[-1]['rank']
            msg += f"{i.mention} is rank {rank} \n\n"

        print(msg)
        await message.channel.send(msg)


@client.event
async def on_raw_reaction_add(payload):
    if payload.user_id == client.user.id:
        return

    member_role_ids = list(map(lambda role: str(role.id), payload.member.roles))

    if STAFF_ID not in member_role_ids:
        print("someone reacted, but they're not staff")
        return

    query = Query()
    pen = pending.search(query.message_id == payload.message_id)[0]

    if str(payload.emoji) == "👍":
        pending.remove(where('message_id') == payload.message_id)
        users.update(where('name') == pen['user'], increment('rank'))
    elif (str(payload.emoji) == "👎"):
        print("thumbsdown from mod")
        pending.remove(where('message_id') == payload.message_id)
    else: print(payload.emoji)



client.run(TOKEN)