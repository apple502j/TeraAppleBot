import traceback, sys
import discord
from discord.ext import commands
from .stars import StarError

class Error(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, err):
        if isinstance(err, commands.UserInputError):
            return await ctx.say("error.args", ctx.command.qualified_name)
        elif isinstance(err, commands.CommandNotFound):
            return await ctx.say("error.notfound")
        elif isinstance(err, commands.PrivateMessageOnly):
            return await ctx.say("error.noguild")
        elif isinstance(err, commands.NoPrivateMessage):
            return await ctx.say("error.nodm")
        elif isinstance(err, commands.NotOwner):
            return await ctx.say("error.notowner")
        elif isinstance(err, commands.MissingPermissions):
            return await ctx.say("error.noperms", ", ".join(err.missing_perms))
        elif isinstance(err, commands.BotMissingPermissions):
            return await ctx.say("error.botnoperms", ", ".join(err.missing_perms))
        elif isinstance(err, commands.DisabledCommand):
            return await ctx.say("error.disabled")
        elif isinstance(err, commands.CommandOnCooldown):
            return await ctx.say("error.cooldown", err.retry_after)
        elif isinstance(err, StarError):
            return await ctx.send(err.message)
        else:
            traceback.print_exception(type(err), err, err.__traceback__, file=sys.stderr)

def setup(bot):
    bot.add_cog(Error(bot))
