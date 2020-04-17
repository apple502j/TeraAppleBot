import uuid
from discord.ext import commands
from .utils import Command

class UUIDCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="uuid", id=35, cls=Command)
    async def get_uuid(self, ctx):
        await ctx.send(uuid.uuid4().urn.lower()[9:])

setup = lambda bot: bot.add_cog(UUIDCog(bot))