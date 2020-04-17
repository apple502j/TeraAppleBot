import discord
from discord.ext import commands
from .utils import Command

SEED = 0x31415926535897932

class SurveyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def to_sc(n):
        return (n - 0x14142) ^ SEED

    @staticmethod
    def from_sc(N):
        return (N ^ SEED) + 0x14142

    @commands.command(id=39, cls=Command)
    async def survey_code(self, ctx):
        code = self.to_sc(ctx.author.id)
        await ctx.author.send(f"あなたのコードは`{code}`です。")

    @commands.command(id=40, cls=Command, hidden=True)
    @commands.is_owner()
    async def sc2id(self, ctx, N):
        await ctx.author.send(f"the code is {self.from_sc(N)}")

def setup(bot):
    bot.add_cog(SurveyCog(bot))
