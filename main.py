import json, random, asyncio, os, time
import discord
from discord.ext import commands
from dotenv import load_dotenv
import pymongo
from pymongo import MongoClient
load_dotenv()

prefix = 'v!'
client = commands.Bot(command_prefix = prefix)
db = MongoClient(os.environ.get('MONGODB_URI'))['vysogota']

def check_exists(uid):
    exists = db.users.find_one({'_id': uid})
    if exists is not None:
        return True
    else:
        return False
    
def add_points(uid, amount):
    if check_exists(uid):
        db.users.update_one({'_id': uid}, {'$inc': {'points': amount}})
    else:
        user = {
            '_id': uid,
            'points': 0
        }
        db.users.insert_one(user)
        db.users.update_one({'_id': uid}, {'$inc': {'points': amount}})

def random_character():
    with open('characters.json') as f:
        character = random.choice(json.load(f))
    return character

@client.event
async def on_ready():
    client.remove_command('help')
    await client.change_presence(activity = discord.Game('v!pomoc'))
    print('Bot ready.')

@client.command(name = 'kimjestem', aliases = ['kj'])
async def guess_character(ctx):
    character = random_character()
    name = character['name']
    img_url = character['imgUrl']

    question_embed = discord.Embed(colour = 0xae986b, title = 'Kim jestem?')
    question_embed.set_author(icon_url = client.user.avatar_url, name = str(client.user))
    question_embed.set_image(url = img_url)
    await ctx.send(embed = question_embed)
    start = time.time()

    def correct_answer(message):
        if not message.author.bot:
            return message.content.lower() in name.lower().split(' ') or message.content.lower() == name.lower()
        else:
            return False

    try:
        msg = await client.wait_for('message', check = correct_answer, timeout = 10.0)
        winner = msg.author
        answer_time = time.time() - start
        points = round(100 - answer_time * 10)
        winner_embed = discord.Embed(colour = 0xae986b, description = f'{winner.mention} wygrał z wynikiem **{points}**.\n Postać: **{name}**.')
        winner_embed.set_author(icon_url = client.user.avatar_url, name = str(client.user))
        add_points(winner.id, points)
        await ctx.send(embed = winner_embed)
    
    except asyncio.TimeoutError:
        answer_embed = discord.Embed(
            colour = 0xae986b,
            title = 'Koniec czasu!',
            description = f'Postać: **{name}**.',
            )
        await ctx.send(embed = answer_embed)

@client.command(name = 'pomoc')
async def help(ctx):
    embed = discord.Embed(
        colour = 0xae986b,
        title = 'Vysogota',
        description = 'Vysogota to BOT na Discorda, który sprawdzi twoją wiedzę na temat postaci z uniwersum Wiedźmina.',
    )
    embed.set_thumbnail(url = client.user.avatar_url)
    embed.add_field(name = 'v!kimjestem', value = 'Rozpoczyna zgadywanie postaci.', inline = False)
    embed.add_field(name = 'v!punkty', value = 'Pokazuje aktualną ilość punktów', inline = False)
    embed.add_field(name = 'v!tabela', value = 'Pokazuje globalną tabelę wyników.', inline = False)

    await ctx.send(embed = embed)

@client.command(name = 'punkty')
async def points(ctx):
    points = db.users.find_one({'_id': ctx.message.author.id})
    if points is None:
        num_points = 0
    else:
        num_points = points['points']
    embed = discord.Embed(colour = 0xae986b, title = num_points)
    embed.set_author(icon_url = ctx.message.author.avatar_url, name = str(ctx.message.author))
    await ctx.send(embed = embed)

@client.command(name = 'tabela')
async def leaderboard(ctx):
    users = db.users.find({}).sort('points', pymongo.DESCENDING)
    board = ''
    pos = 1
    for user in users:
        username = str(await client.fetch_user(user['_id']))
        points = user['points']
        entry = f'{pos}. **{username}** - {points}'
        board += f'{entry}\n'
        pos += 1
    embed = discord.Embed(colour = 0xae986b, title = 'Leaderboard', description = board)
    embed.set_thumbnail(url = 'https://i.imgur.com/1Jh5dm9.png')
    embed.set_author(icon_url = client.user.avatar_url, name = str(client.user))
    await ctx.send(embed = embed)

if __name__ == '__main__':
    client.run(os.environ.get('TOKEN'))