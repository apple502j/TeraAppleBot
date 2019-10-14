import random
import discord
from discord.ext import commands
from .utils import Command

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(id=10, cls=Command)
    async def stats(self, ctx):
        """Statistics about me."""
        embed = discord.Embed(
            title=ctx._("stats.title"),
            description=ctx._("stats.description"),
            color=random.randint(0,0xFFFFFF)
        )

        embed.add_field(
            name=ctx._("stats.guilds"),
            value=ctx._("stats.guildsDetail",
                len(self.bot.guilds),
                len([g for g in self.bot.guilds if not g.unavailable]),
                len([g for g in self.bot.guilds if g.unavailable]),
            ),
            inline=True
        )

        embed.add_field(
            name=ctx._("stats.users"),
            value=ctx._("stats.usersDetail",
                len(self.bot.users),
                len([u for u in self.bot.users if not u.bot]),
                len([u for u in self.bot.users if u.bot]),
            ),
            inline=True
        )

        embed.add_field(
            name=ctx._("stats.members"),
            value=ctx._("stats.membersDetail",
                len(list(self.bot.get_all_members())),
                len([u for u in self.bot.users if self.bot.get_member(u.id).status is discord.Status.online]),
                len([u for u in self.bot.users if self.bot.get_member(u.id).status is discord.Status.idle]),
                len([u for u in self.bot.users if self.bot.get_member(u.id).status is discord.Status.dnd]),
                len([u for u in self.bot.users if self.bot.get_member(u.id).status is discord.Status.offline]),
            ),
            inline=True
        )

        ch = list(self.bot.get_all_channels())

        embed.add_field(
            name=ctx._("stats.channels"),
            value=ctx._("stats.channelsDetail",
                len(ch),
                len([c for c in ch if c.type is discord.ChannelType.text]),
                len([c for c in ch if c.type is discord.ChannelType.voice]),
            ),
            inline=True
        )

        embed.add_field(
            name=ctx._("stats.emojis"),
            value=ctx._("stats.emojisDetail",
                len(self.bot.emojis),
                len([e for e in self.bot.emojis if e.animated]),
                len([e for e in self.bot.emojis if not e.animated]),
            ),
            inline=True
        )

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Stats(bot))
