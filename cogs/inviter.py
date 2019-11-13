import discord
from discord.ext import commands
from .utils import perms, Command

class Inviter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        required = perms(
            read_messages=True,
            send_messages=True,
            read_message_history=True,
            embed_links=True,
            external_emojis=True,
            attach_files=True
        )
        bot.perms = self.perms = {
            "all": required,
            "starboard": perms(
                required,
                manage_messages=True,
                manage_roles=True,
                manage_channels=True
            )
        }

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Add me to a server with {discord.utils.oauth_url(self.bot.user.id, self.perms['all'])}")

    @commands.command(id=32, cls=Command)
    async def invite(self, ctx, kind="all"):
        """Gets my invite. kind can be omitted for basic permissions, and can be `starboard` for starboard."""
        if kind in self.perms:
            url = discord.utils.oauth_url(self.bot.user.id, self.perms[kind])
            desc = ctx._(f"inviter.{kind}Type")
            embed = discord.Embed(
                title=desc,
                description=f"[{ctx._('inviter.invite')}]({url})",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.say("inviter.notsuch")

def setup(bot):
    bot.add_cog(Inviter(bot))
