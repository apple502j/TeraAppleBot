import discord
from discord.ext import commands

class Inviter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Add me to a server with {discord.utils.oauth_url(self.bot.user.id, discord.Permissions.all())}")

def setup(bot):
    bot.add_cog(Inviter(bot))
