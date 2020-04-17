import random
import json
import asyncio
import traceback
import sys

import discord
from discord.ext import commands
from .utils import Command

EMOJIS = [f"{n+1}\U0000fe0f\U000020e3" for n in range(4)]

class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("sounds.json", "r", encoding="utf-8") as f:
            self.sounds = json.load(f)

    @commands.Cog.listener()
    async def on_ready_once(self):
        for g in self.bot.guilds:
            for ch in g.voice_channels:
                if g.me in ch.members and ch.permissions_for(g.me).move_members:
                    await g.me.edit(voice_channel=None)
                    break

    def can_voice(self, ch):
        p = ch.permissions_for(ch.guild.me)
        return ch.user_limit != len(ch.members) and p.connect and p.speak

    def get_vc(self, ctx):
        if ctx.voice_client:
            return ctx.voice_client.channel
        if ctx.author.voice and self.can_voice(ctx.author.voice.channel):
            return ctx.author.voice.channel
        if ctx.channel.category:
            same_cat = ctx.channel.category.voice_channels
        else:
            same_cat = [ch for ch in ctx.guild.voice_channels if ch.category is None]
        same_cat = [ch for ch in same_cat if self.can_voice(ch)]
        if same_cat:
            return same_cat[0]
        all_guild = [ch for ch in ctx.guild.voice_channels if self.can_voice(ch)]
        if all_guild:
            return all_guild[0]
        return None

    @commands.command(id=41, cls=Command)
    @commands.guild_only()
    @commands.max_concurrency(1, commands.BucketType.guild)
    async def music_quiz(self, ctx):
        bot = self.bot
        vc = self.get_vc(ctx)
        if not vc:
            return await ctx.say("voice.noVC")
        if ctx.voice_client:
            vcl = ctx.voice_client
        else:
            vcl = await vc.connect()
        item = random.choice(self.sounds)
        name = ctx._(item["name"])
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f"sounds/{item['file']}"))
        random_choices = random.sample([ctx._(i["name"]) for i in self.sounds if i != item], 3)
        choices = random.sample([name, *random_choices], 4)
        choices_formatted = [f"{n+1}) {choices[n]}" for n in range(4)]
        msg = await ctx.say("voice.musicQuizDescription", "\n".join(choices_formatted))
        await asyncio.gather(*[msg.add_reaction(EMOJIS[n]) for n in range(4)])
        def after(exception):
            if exception:
                traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)
            self.bot.dispatch("voice_finished", ctx)
        vcl.play(source, after=after)
        done, pending = await asyncio.wait([
                    bot.wait_for('voice_finished', check=lambda _ctx: ctx==_ctx),
                    bot.wait_for('reaction_add', check=lambda r,u:all([
                        u in vc.members,
                        u != ctx.me,
                        str(r.emoji) in EMOJIS,
                        r.message.id == msg.id
                    ]))
                ], return_when=asyncio.FIRST_COMPLETED)

        vcl.stop()
        await vcl.disconnect()
        try:
            stuff = done.pop().result()
            if not isinstance(stuff, tuple):
                return await ctx.say("voice.timeout", name)
            else:
                em = str(stuff[0].emoji)
                n = EMOJIS.index(em)
                if choices[n] == name:
                    return await ctx.say("voice.correct", str(stuff[1]))
                else:
                    return await ctx.say("voice.incorrect", name)
        except asyncio.TimeoutError:
            # shouldn't be called
            for future in pending:
                future.cancel()


def setup(bot):
    bot.add_cog(Voice(bot))
