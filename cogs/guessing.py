import os, time, random, json, asyncio

import discord
from discord.ext import commands

from database import (
    db,
    check_exists,
    assign_to_guild,
    user_assigned_to_guild, 
    create_user, 
    add_points
)

class Guessing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name = 'kimjestem', aliases = ['kj'])
    @commands.cooldown(1, 7, commands.BucketType.user)
    async def _guess_character(self, ctx):

        with open('characters.json', encoding='utf-8') as f:
            character = random.choice(json.load(f))
        
        name = character['name']
        img_url = character['imgUrl']

        question_embed = discord.Embed(colour = 0xae986b, title = 'Kim jestem?')
        question_embed.set_author(icon_url = self.bot.user.avatar_url, name = str(self.bot.user))
        question_embed.set_image(url = img_url)
        await ctx.send(embed = question_embed)
        start = time.time()

        def correct_answer(message):
            if not message.author.bot and message.channel == ctx.message.channel:
                return message.content.lower() in name.lower().split(' ') or message.content.lower() == name.lower()
            else:
                return False

        try:
            msg = await self.bot.wait_for('message', check = correct_answer, timeout = 10.0)
            winner = msg.author
            answer_time = time.time() - start
            points = round(100 - answer_time * 10)
            winner_embed = discord.Embed(colour = 0xae986b, description = f'{winner.mention} wygrał z wynikiem **{points}**.\n Postać: **{name}**.')
            winner_embed.set_author(icon_url = self.bot.user.avatar_url, name = str(self.bot.user))
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

def setup(bot):
    bot.add_cog(Guessing(bot))
  
