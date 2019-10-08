import discord
from discord.ext import commands

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx):
        await ctx.send(ctx._("basic.hello"))

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(ctx._("basic.ping", round(self.bot.latency*100)/100))

    @commands.command()
    async def repeat(self, ctx, *, text=''):
        msg = await ctx.send(discord.utils.escape_mentions(text))
        self.bot.db.execute("INSERT INTO pending_delete values (?,?,?)", (ctx.message.id, ctx.channel.id, msg.id))

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

def setup(bot):
    bot.add_cog(Basic(bot))
