from datetime import datetime
import discord
from discord.ext import commands
from .utils import Group, within

class OnlineNotif(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        def shares_guild(user_id_a, user_id_b):
            return not not [
                guild
                for guild
                in self.bot.guilds
                if set([user_id_a, user_id_b]).issubset(frozenset(i.id for i in guild.members))
            ]
        self.bot.shares_guild = shares_guild
        def get_member(user_id):
            return discord.utils.get(list(self.bot.get_all_members()), id=user_id)
        self.bot.get_member = get_member

        self._last_posted = {}

    def get_subscribers(self):
        return [
            {"user_id": int(i["user_id"]), "subscribe": [int(j) for j in (i["subscribe"] or "").split(",") if j]}
            for i
            in self.bot.db.execute("SELECT user_id, subscribe FROM users").fetchall()
        ]

    def get_subscribing_of_user(self, user):
        return discord.utils.find(lambda item:item["user_id"] == user.id, self.get_subscribers())["subscribe"]

    def get_subscribed_of_user(self, user):
        return [
            i["user_id"]
            for i
            in self.get_subscribers()
            if user.id in i["subscribe"]
        ]

    def onlinenotif_enabled(self, user):
        enabled = self.bot.db.execute("SELECT online_agreed FROM users WHERE user_id = ?", (user.id,)).fetchone()
        return enabled and enabled["online_agreed"]

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.status == after.status:
            return
        if before.status != discord.Status.offline:
            return
        if not self.onlinenotif_enabled(before):
            return
        if self._last_posted.get(before.id, None) and within(self._last_posted[before.id], 3):
            return
        self._last_posted[before.id] = datetime.utcnow()
        for subsc in self.get_subscribed_of_user(before):
            if self.bot.shares_guild(before.id, subsc) and self.bot.get_member(subsc).status != discord.Status.offline:
                user = self.bot.get_user(subsc)
                await user.send(self.bot._("onlinenotif.notif", user, str(before)))

    @commands.group(invoke_without_command=True, id=8, cls=Group)
    async def onlinenotif(self, ctx):
        """Returns the name of the users you are receiving online notifications of."""
        users = [
            self.bot.get_user(user_id)
            for user_id
            in self.get_subscribing_of_user(ctx.author)
            if self.bot.shares_guild(ctx.author.id, user_id)
        ]
        if not users:
            return await ctx.author.send(ctx._("onlinenotif.nousers"))
        await ctx.author.send(ctx._("onlinenotif.subscribing", " ".join(map(str, users))))

    @onlinenotif.command(aliases=["add"])
    async def subscribe(self, ctx, user: discord.User):
        """Subscribes to this user."""
        subscribing = self.get_subscribing_of_user(ctx.author)
        if user.id in subscribing:
            return await ctx.say("onlinenotif.already")
        if not self.bot.shares_guild(ctx.author.id, user.id):
            return await ctx.say("onlinenotif.shareGuild")
        new_value = ",".join(map(str, subscribing + [user.id]))
        ctx.db.execute("UPDATE users SET subscribe = ? WHERE user_id = ?",(new_value, ctx.author.id))
        await ctx.say("onlinenotif.success")

    @onlinenotif.command(aliases=["remove", "del"])
    async def unsubscribe(self, ctx, user: discord.User):
        """Un-subscribes to this user."""
        subscribing = self.get_subscribing_of_user(ctx.author)
        if user.id not in subscribing:
            return await ctx.say("onlinenotif.yet")
        subscribing.remove(user.id)
        new_value = ",".join(subscribing)
        ctx.db.execute("UPDATE users SET subscribe = ? WHERE user_id = ?",(new_value, ctx.author.id))
        await ctx.say("onlinenotif.removeSuccess")

    @onlinenotif.command()
    async def settings(self, ctx, enabled: bool = False):
        """Choose whether someone can receive your online notification.
        Note that you have to share server with that user."""
        ctx.db.execute("UPDATE users SET online_agreed = ? WHERE user_id = ?", (int(enabled), ctx.author.id))
        await ctx.say("onlinenotif.settings")


def setup(bot):
    bot.add_cog(OnlineNotif(bot))
