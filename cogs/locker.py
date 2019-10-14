import discord
from discord.ext import commands
from .utils import Command

class Locker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        def get_cmd(command_id):
            return discord.utils.find(lambda c: getattr(c, "id", None) == command_id, bot.commands)
        self.bot.get_cmd = get_cmd
        def is_locked(guild_id, command_id):
            bit = self.bot.db.execute("SELECT disabled_flag FROM guilds WHERE guild_id = ?", (guild_id,)).fetchone()[0]
            return bit & 1<<command_id
        self.bot.is_locked = is_locked
        def store_guild(guild):
            if not self.bot.db.execute("SELECT guild_id FROM guilds WHERE guild_id = ?", (guild.id,)).fetchone():
                print(f'DB: Stored guild {guild.id}')
                self.bot.db.execute("INSERT INTO guilds values (?,?)", (guild.id, 0))
        self.bot.store_guild = store_guild

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.bot.store_guild(guild)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.bot.store_guild(guild)

    @commands.command(id=18, cls=Command)
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def lock(self, ctx, command_id:int):
        """Locks a command."""
        if command_id in (18, 19):
            return await ctx.say("locker.cannot")
        if not self.bot.get_cmd(command_id):
            return await ctx.say("locker.notFound")
        if self.bot.is_locked(ctx.guild.id, command_id):
            return await ctx.say("locker.already")
        bit = self.bot.db.execute("SELECT disabled_flag FROM guilds WHERE guild_id = ?", (ctx.guild.id,)).fetchone()[0]
        bit |= 1 << command_id
        self.bot.db.execute("UPDATE guilds SET disabled_flag = ? WHERE guild_id = ?", (bit, ctx.guild.id))
        await ctx.say("locker.success")

    @commands.command(id=19, cls=Command)
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def unlock(self, ctx, command_id:int):
        """Unlocks a command."""
        if command_id in (18, 19):
            return await ctx.say("locker.cannot")
        if not self.bot.get_cmd(command_id):
            return await ctx.say("locker.notFound")
        if not self.bot.is_locked(ctx.guild.id, command_id):
            return await ctx.say("locker.yet")
        bit = self.bot.db.execute("SELECT disabled_flag FROM guilds WHERE guild_id = ?", (ctx.guild.id,)).fetchone()[0]
        bit ^= 1 << command_id
        self.bot.db.execute("UPDATE guilds SET disabled_flag = ? WHERE guild_id = ?", (bit, ctx.guild.id))
        await ctx.say("locker.successUnlock")

    async def bot_check_once(self, ctx):
        if ctx.guild is None:
            return True
        if not hasattr(ctx.command, "id"):
            return True
        if self.bot.is_locked(ctx.guild.id, ctx.command.id):
            await ctx.say("locker.locked")
            return False
        return True


def setup(bot):
    bot.add_cog(Locker(bot))
