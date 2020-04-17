import discord
from discord.ext import commands

from .utils import Command

MEE6_URL = "https://mee6.xyz/api/plugins/levels/leaderboard/{}"
RAW_ICON = "https://cdn.discordapp.com/{}s/{}/{}.png?size=512"

class MEE6(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(id=34, cls=Command, hidden=True)
    async def mee6(self, ctx, guild_id: int = 0):
        """Shows MEE6 Leaderboard."""
        if not guild_id > 0:
            if ctx.guild:
                guild_id = ctx.guild.id
            else:
                return await ctx.say("mee6.invalid")
        async with self.bot.session.get(MEE6_URL.format(guild_id)) as rsp:
            if rsp.status >= 400:
                return await ctx.say("mee6.unavailable")
            result = await rsp.json()
        embed = discord.Embed(
            title=ctx._("mee6.title", result["guild"]["name"], result["guild"]["id"]),
            description=ctx._(
                "mee6.description",
                result["xp_per_message"][0],
                result["xp_per_message"][1],
                result["xp_rate"]
            ),
            color=ctx.author.color or 0x777777,
            timestamp=ctx.message.created_at
        )
        embed.set_thumbnail(url=RAW_ICON.format("icon", result["guild"]["id"], result["guild"]["icon"]))
        embed.add_field(name=ctx._("mee6.exampleName"), value=ctx._("mee6.exampleValue"), inline=False)
        for member in result["players"][:25]:
            embed.add_field(
                name=ctx._(
                    "mee6.name",
                    member["username"],
                    member["discriminator"],
                    member["id"],
                    member["level"]
                ),
                value=ctx._(
                    "mee6.value",
                    ctx._("mee6.avatar"),
                    RAW_ICON.format("avatar", member["id"], member["avatar"]),
                    member["xp"],
                    member["message_count"]
                ),
                inline=True
            )
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(MEE6(bot))
