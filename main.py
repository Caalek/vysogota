import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

intents = discord.Intents.default()
intents.members = True
prefixes = ['v!', 'V!']
bot = commands.Bot(
    command_prefix = prefixes,
    case_insensitive = True,
    intents = intents)

@bot.event
async def on_ready():
    bot.remove_command('help')
    for cog in os.listdir('cogs'):
        if cog.endswith('.py'):
            cog = cog.replace('.py', '')
            bot.load_extension(f'cogs.{cog}')
    await bot.change_presence(activity = discord.Game('v!pomoc'))
    print('Bot ready.')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(colour = 0xae986b, description = f'{ctx.author.mention}, kolejny raz możesz użyć tej komendy za **{round(error.retry_after)}** sekund!')
        await ctx.send(embed = embed)
    elif isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(colour = 0xae986b, description = 'Ta komenda nie istnieje.')
        await ctx.send(embed = embed)
    else:
        raise error

@bot.command(name = 'pomoc')
async def _help(ctx):
    embed = discord.Embed(
        colour = 0xae986b,
        title = 'Vysogota',
        description = 'Vysogota to BOT na Discorda, który sprawdzi twoją wiedzę na temat postaci z uniwersum Wiedźmina.',
    )
    embed.set_thumbnail(url = bot.user.avatar_url)
    embed.add_field(name = 'v!kj', value = 'Rozpoczyna zgadywanie postaci.', inline = False)

    embed.add_field(name = 'v!tabela', value = 'Pokazuje serwerową tabelę wyników.', inline = False)
    embed.add_field(name = 'v!punkty', value = 'Pokazuje liczbę punktów.', inline = False)

    await ctx.send(embed = embed)

if __name__ == '__main__':
    bot.run(os.environ.get('TOKEN'))