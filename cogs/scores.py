import discord, pytz
from discord.ext import commands

import os

from database import db
from datetime import datetime

class Scores(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        allowed_reactions = ['⬅', '➡']
        if not user.bot and reaction.emoji in allowed_reactions:
            channel = reaction.message.channel
            message = reaction.message
            scores = await self.get_guild_scores(reaction.message.channel.guild.id)
            emoji = reaction.emoji
            last_score = int(message.embeds[0].description.split('\n')[-1].split('.')[0])
            first_score = int(message.embeds[0].description.split('\n')[0].split('.')[0])

            if reaction.emoji == '➡':
                formatted_scores = self.format_guild_scores(scores, last_score, last_score + 20)
            elif reaction.emoji == '⬅':
                second_number = last_score - 20
                if second_number % 20 != 0:
                    for i in range(second_number - 20, second_number + 20):
                        if i % 20 == 0:
                            second_number = i
                formatted_scores = self.format_guild_scores(scores, first_score - 21, second_number)
                
            if formatted_scores == '':
                await message.remove_reaction(reaction.emoji, user)
            else:
                embed = discord.Embed(colour = 0xae986b, title = str(channel.guild), description = formatted_scores)
                embed.set_thumbnail(url = 'https://i.imgur.com/1Jh5dm9.png')
                embed.set_author(icon_url = self.bot.user.avatar_url, name = str(self.bot.user))
                tz = pytz.timezone(os.getenv('TZ'))
                embed.set_footer(text = f'Zaktualizowano {datetime.now(tz).strftime("%d.%m.%Y o %H:%M:%S")}')
                await message.edit(embed = embed)
                await message.remove_reaction(reaction.emoji, user)
    
    async def get_guild_scores(self, guild_id):
        users = db.users.find({})
        guild_scores = []
        for user in users:
            for guild in user['guilds']:
                if guild['guild_id'] == guild_id:
                    new_user = self.bot.get_user(user['_id'])
                    #new_user = await bot.fetch_user(user['_id'])
                    guild['user'] = new_user
                    if new_user is not None:
                        guild_scores.append(guild)
        sorted_guild_scores = sorted(guild_scores, key = lambda k: k['points'], reverse=True)
        return sorted_guild_scores

    def format_guild_scores(self, scores, start, end):
        pos = start + 1
        board = ''
        
        for score in scores[start:end]:
            user = score['user'].mention
            points = score['points']
            entry = f'{pos}. **{user}** - {points}'
            board += f'{entry}\n'
            pos += 1
        return board

    @commands.command(name = 'tabela')
    async def _leaderboard(self, ctx):
        board = ''
        pos = 1
        sorted_guild_scores = await self.get_guild_scores(ctx.message.guild.id)

        board = self.format_guild_scores(sorted_guild_scores, 0, 20)
                
        embed = discord.Embed(colour = 0xae986b, title = str(ctx.guild), description = board)
        embed.set_thumbnail(url = 'https://i.imgur.com/1Jh5dm9.png')
        embed.set_author(icon_url = self.bot.user.avatar_url, name = str(self.bot.user))
        tz = pytz.timezone(os.getenv('TZ'))
        embed.set_footer(text = f'Wysłano {datetime.now(tz).strftime("%d.%m.%Y o %H:%M:%S")}')
        message = await ctx.send(embed = embed)
        await message.add_reaction('⬅')
        await message.add_reaction('➡')
    
    @commands.command(name = 'punkty')
    async def _points(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        member_doc = db.users.find_one({'_id': member.id})
        for i in member_doc['guilds']:
            if i['guild_id'] == ctx.message.guild.id:
                points = i['points']
        embed = discord.Embed(colour = 0xae986b, title = points)
        embed.set_author(icon_url = member.avatar_url, name = str(member))
        await ctx.send(embed = embed)

def setup(bot):
    bot.add_cog(Scores(bot))