import asyncio
import discord
from discord.ext import commands

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.owner_only = False
        async def is_banned(user_id):
            if await self.bot.is_owner(discord.Object(user_id)):
                return False
            ban = self.bot.db.execute("SELECT banned FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return ban and ban["banned"]
        self.bot.is_banned = is_banned

    async def cog_check_once(self, ctx):
        if await self.bot.is_owner(ctx.author):
            return True
        raise commands.NotOwner("Owner cog is for me")

    async def bot_check_once(self, ctx):
        if await self.bot.is_owner(ctx.author):
            return True
        return not (self.bot.owner_only or await self.bot.is_banned(ctx.author.id))

    # We don't have IDs for these commands. Why? Because ID is just for locking.
    @commands.group()
    async def owner(self, ctx):
        pass

    @owner.command()
    async def ban(self, ctx, user: discord.User):
        if user.bot:
            return await ctx.say("owner.bot")
        if await self.bot.is_owner(user):
            return await ctx.say("owner.you")
        if await self.bot.is_banned(user.id):
            return await ctx.say("owner.already")
        self.bot.db.execute("UPDATE users SET banned = 1 WHERE user_id = ?", (user.id,))
        await ctx.say("owner.done")

    @owner.command()
    async def unban(self, ctx, user: discord.User):
        if user.bot:
            return await ctx.say("owner.bot")
        if await self.bot.is_owner(user):
            return await ctx.say("owner.you")
        if not await self.bot.is_banned(user.id):
            return await ctx.say("owner.yet")
        self.bot.db.execute("UPDATE users SET banned = 0 WHERE user_id = ?", (user.id,))
        await ctx.say("owner.done")

    @owner.command()
    async def leave(self, ctx, guild = None):
        if guild is None:
            guild = ctx.guild
        else:
            guild = self.bot.get_guild(guild)
        if guild is None:
            raise commands.NoPrivateMessage("leave without argument must be done inside guild")
        await ctx.say("owner.leaveTimeout")
        try:
            await self.bot.wait_for("message", check=lambda msg: all([
                msg.channel == ctx.channel,
                msg.author == ctx.author,
                msg.content == "LEAVE GUILD"
            ]), timeout=10)
        except asyncio.TimeoutError:
            self.destroy_starboard(ctx.channel.id, ctx.guild.id)
            await ctx.say("owner.kept")
        else:
            await guild.leave()

    @owner.command()
    async def only(self, ctx, enabled:bool = False):
        self.bot.owner_only = enabled
        await ctx.say("owner.only", enabled)

def setup(bot):
    bot.add_cog(Owner(bot))
