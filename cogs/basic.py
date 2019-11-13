import discord
from discord.ext import commands
from .utils import Command

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        _exec = bot.db.execute
        bot._db = _db = bot.db
        class DBMock:
            def __getattr__(self, attr):
                if attr == "execute":
                    def execute(text, param=None):
                        print(f"SQL: {text}")
                        return _exec(text, param) if param else _exec(text)
                    return execute
                else:
                    return getattr(_db, attr)
            def execute(self, text, param=None):
                print(f"SQL: {text}")
                return _exec(text, param) if param else _exec(text)
        #bot.db = DBMock()

    @commands.command(id=3, cls=Command)
    async def hello(self, ctx):
        """Say hello."""
        await ctx.say("basic.hello")

    @commands.command(id=4, cls=Command)
    async def ping(self, ctx):
        """Ping"""
        await ctx.say("basic.ping", round(self.bot.latency*100)/100)

    @commands.command(id=5, cls=Command)
    async def credits(self, ctx):
        """Show credits."""
        await ctx.say("basic.credits")

    @commands.command(id=6, cls=Command)
    async def repeat(self, ctx, *, text=''):
        """Repeats what you said and deletes when you delete. at-everyone attack prevention available"""
        msg = await ctx.send(discord.utils.escape_mentions(text))
        ctx.db.execute("INSERT INTO pending_delete values (?,?,?)", (ctx.message.id, ctx.channel.id, msg.id))

    async def delete_handler(self, message_id):
        pending = self.bot.db.execute("SELECT * FROM pending_delete WHERE original_id = ?", (message_id,)).fetchone()
        if pending:
            await self.bot.http.delete_message(pending["channel_id"], pending["target_id"])

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        await self.delete_handler(payload.message_id)

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        for i in payload.message_ids:
            await self.delete_handler(i)

    @commands.command(id=21, cls=Command)
    @commands.is_owner()
    async def largest_id(self, ctx):
        await ctx.send(sorted(self.bot.walk_commands(), key=lambda cmd: getattr(cmd, "id", -1), reverse=True)[0].id)

def setup(bot):
    bot.add_cog(Basic(bot))
