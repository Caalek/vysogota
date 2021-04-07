import json, random, asyncio, os, time, pytz
import discord
from discord.ext import commands
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.reactions = True
prefixes = ['v!', 'V!']
client = commands.Bot(
    command_prefix = prefixes,
    case_insensitive = True,
    intents = intents)
db = MongoClient(os.environ.get('MONGODB_URI'))['vysogota']
tz = pytz.timezone('Europe/Warsaw')

def check_exists(uid):
    exists = db.users.find_one({'_id': uid})
    if exists is not None:
        return True
    else:
        return False

def create_user(uid):
    user = {
            '_id': uid,
            'guilds': []
        }
    db.users.insert_one(user)

def user_assigned_to_guild(uid, guild_id):
    users_guilds = db.users.find_one({'_id': uid})['guilds']
    for i in users_guilds:
        if i['guild_id'] == guild_id:
            return True
    else:
        return False

def assign_to_guild(uid, guild_id):
    guild = {
        'guild_id': guild_id,
        'points': 0,
        }
    db.users.update_one({'_id': uid}, {'$push': {'guilds': guild}})

def add_points(uid, guild_id, amount):
    user = db.users.find_one({'_id': uid})
    user_guilds = user['guilds']
    for i in user_guilds:
        if i['guild_id'] == guild_id:
            index = user_guilds.index(i)
            break
            
    db.users.update_one({'_id': uid}, {'$inc': {f'guilds.{index}.points': amount}})

def random_character():
    with open('characters.json') as f:
        character = random.choice(json.load(f))
    return character

async def get_guild_scores(guild_id):
    users = db.users.find({})
    guild_scores = []
    for user in users:
        for guild in user['guilds']:
            if guild['guild_id'] == guild_id:
                new_user = client.get_user(user['_id'])
                #    new_user = await client.fetch_user(user['_id'])
                guild['user'] = new_user
                if new_user is not None:
                    guild_scores.append(guild)
    sorted_guild_scores = sorted(guild_scores, key = lambda k: k['points'], reverse=True)
    return sorted_guild_scores

def format_guild_scores(scores, start, end):
    pos = start + 1
    board = ''
    
    for score in scores[start:end]:
        user = score['user']
        points = score['points']
        entry = f'{pos}. **{user}** - {points}'
        board += f'{entry}\n'
        pos += 1
    return board


@client.event
async def on_ready():
    client.remove_command('help')
    await client.change_presence(activity = discord.Game('v!pomoc'))
    print('Bot ready.')

@client.event
async def on_reaction_add(reaction, user):
    if not user.bot:
        channel = reaction.message.channel
        message = reaction.message
        scores = await get_guild_scores(reaction.message.channel.guild.id)
        emoji = reaction.emoji
        last_score = int(message.embeds[0].description.split('\n')[-1].split('.')[0])
        first_score = int(message.embeds[0].description.split('\n')[0].split('.')[0])

        if reaction.emoji == '➡':
            formatted_scores = format_guild_scores(scores, last_score, last_score + 20)
        elif reaction.emoji == '⬅':
            formatted_scores = format_guild_scores(scores, first_score - 21, round(last_score/10)* 10 - 20)
        
        if formatted_scores == '':
            await message.remove_reaction(reaction.emoji, user)
        else:
            embed = discord.Embed(colour = 0xae986b, title = str(channel.guild), description = formatted_scores)
            embed.set_thumbnail(url = 'https://i.imgur.com/1Jh5dm9.png')
            embed.set_author(icon_url = client.user.avatar_url, name = str(client.user))
            embed.set_footer(text = f'Wysłano {datetime.now(tz).strftime("%d.%m.%Y o %H:%M:%S")}')
            await message.edit(embed = embed)
            await message.remove_reaction(reaction.emoji, user)



@client.command(name = 'kimjestem', aliases = ['kj'])
async def _guess_character(ctx):
    character = random_character()
    name = character['name']
    img_url = character['imgUrl']

    question_embed = discord.Embed(colour = 0xae986b, title = 'Kim jestem?')
    question_embed.set_author(icon_url = client.user.avatar_url, name = str(client.user))
    question_embed.set_image(url = img_url)
    await ctx.send(embed = question_embed)
    start = time.time()

    def correct_answer(message):
        if not message.author.bot and message.channel == ctx.message.channel:
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
        guild_id = msg.guild.id
        uid = winner.id

        if not check_exists(uid):
            create_user(uid)
        
        if user_assigned_to_guild(uid, guild_id):
            add_points(uid, guild_id, points)
        else:
            assign_to_guild(uid, guild_id)
            add_points(uid, guild_id, points)
        
        await ctx.send(embed = winner_embed)
    
    except asyncio.TimeoutError:
        answer_embed = discord.Embed(
            colour = 0xae986b,
            title = 'Koniec czasu!',
            description = f'Postać: **{name}**.',
            )
        await ctx.send(embed = answer_embed)

@client.command(name = 'pomoc')
async def _help(ctx):
    embed = discord.Embed(
        colour = 0xae986b,
        title = 'Vysogota',
        description = 'Vysogota to BOT na Discorda, który sprawdzi twoją wiedzę na temat postaci z uniwersum Wiedźmina.',
    )
    embed.set_thumbnail(url = client.user.avatar_url)
    embed.add_field(name = 'v!kj', value = 'Rozpoczyna zgadywanie postaci.', inline = False)

    embed.add_field(name = 'v!tabela', value = 'Pokazuje serwerową tabelę wyników.', inline = False)
    embed.add_field(name = 'v!punkty', value = 'Pokazuje liczbę punktów.', inline = False)
    embed.add_field(name = 'v!tabela', value = 'Pokazuje serwerową tabelę wyników.', inline = False)

    await ctx.send(embed = embed)

@client.command(name = 'punkty')
async def punkty(ctx, user: discord.Member = None):
    user = user or ctx.author
    user = db.users.find_one({'_id': user.id})
    for i in user['guilds']:
        if i['guild_id'] == ctx.message.guild.id:
            points = i['points']
    embed = discord.Embed(
        colour = 0xae986b,
        title = points
    )
    embed.set_author(icon_url = user.avatar_url, name = str(user))
    await ctx.send(embed = embed)

@client.command(name = 'tabela')
async def _leaderboard_server(ctx):
    board = ''
    pos = 1
    sorted_guild_scores = await get_guild_scores(ctx.message.guild.id)

    board = format_guild_scores(sorted_guild_scores, 0, 20)
        
    embed = discord.Embed(colour = 0xae986b, title = str(ctx.guild), description = board)
    embed.set_thumbnail(url = 'https://i.imgur.com/1Jh5dm9.png')
    embed.set_author(icon_url = client.user.avatar_url, name = str(client.user))
    embed.set_footer(text = f'Wysłano {datetime.now(tz).strftime("%d.%m.%Y o %H:%M:%S")}')
    message = await ctx.send(embed = embed)
    await message.add_reaction('⬅')
    await message.add_reaction('➡')

if __name__ == '__main__':
    client.run(os.environ.get('TOKEN'))