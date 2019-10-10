import string
from secrets import choice
from random import randint
import datetime
import discord
from discord.ext import commands

class NoCheckHelp(commands.DefaultHelpCommand):
    def __init__(self, **opts):
        super().__init__(**opts)
        self.verify_checks = False

class NotPollOwner(commands.CheckFailure):
    pass

def is_poll_owner():
    def predicate(ctx):
        cond = ctx.db.execute(
            "SELECT * FROM votes WHERE vote_id = ? AND created_by = ?",
            (ctx.message.content.split(" ")[2], ctx.author.id)
        ).fetchone()
        if cond:
            return True
        raise NotPollOwner
    return commands.check(predicate)

class Vote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.old_help = bot.help_command
        bot.help_command = NoCheckHelp()

    def cog_unload(self):
        self.bot.help_command = self.bot.old_help

    def votes(self, vote_id, vote_type):
        if vote_type not in {"yes", "no"}: return
        return [
            int(i)
            for i
            in self.bot.db.execute(f"SELECT {vote_type}_users FROM votes WHERE vote_id = ?", (vote_id,)).fetchone()[0].split(",")
            if i
        ]

    def has_voted(self, vote_id, user_id):
        if user_id in self.votes(vote_id, "yes"):
            return "yes"
        elif user_id in self.votes(vote_id, "no"):
            return "no"
        else:
            return False

    def generate_id(self):
        alphabet = string.ascii_letters + string.digits
        return ''.join(choice(alphabet) for i in range(8))

    def is_available(self, vote_id):
        vote = self.bot.db.execute("SELECT created_at, expires FROM votes WHERE vote_id = ?", (vote_id,)).fetchone()
        now = datetime.datetime.utcnow()
        expires_at = discord.utils.snowflake_time(vote["created_at"]) + datetime.timedelta(hours=vote["expires"])
        return expires_at.timestamp() > now.timestamp()

    @staticmethod
    def get(a,b,default_v):
        try:
            return a[b] if a[b] else ""["what"] # one-line raiser
        except:
            return default_v

    async def cog_command_error(self, ctx, error):
        if isinstance(error, NotPollOwner):
            await ctx.say("vote.notPollOwner")

    @commands.group(invoke_without_command=True)
    async def vote(self, ctx):
        pass

    @vote.command()
    @commands.guild_only()
    async def all(self, ctx):
        """Shows all polls available."""
        all_polls = ctx.db.execute("SELECT vote_id, title FROM votes WHERE guild_id = ?", (ctx.guild.id,)).fetchall()
        all_polls = [poll for poll in all_polls if self.is_available(poll["vote_id"])]
        if not all_polls:
            return await ctx.say("vote.pollNotFound")
        embed = discord.Embed(
            title=ctx._("vote.polls", len(all_polls)),
            description=ctx._("vote.description"),
            timestamp=datetime.datetime.utcnow(),
            color=randint(0, 0xFFFFFF)
        )
        for poll in all_polls:
            embed.add_field(name=poll["vote_id"], value=self.get(poll, "title", ctx._("vote.none")), inline=False)
        await ctx.send(embed=embed)

    @vote.command()
    @commands.guild_only()
    async def info(self, ctx, poll_id):
        """Shows the information about one poll."""
        poll = ctx.db.execute("SELECT * FROM votes WHERE vote_id = ? AND guild_id = ?", (poll_id,ctx.guild.id)).fetchone()
        if not poll:
            return await ctx.say("vote.pollNotFound")
        expires_at = discord.utils.snowflake_time(poll["created_at"]) + datetime.timedelta(hours=poll["expires"])
        embed = discord.Embed(
            title=ctx._("vote.voteTitle", poll["title"]),
            description=self.get(poll, "description", ctx._("vote.none")),
            color=discord.Color.green() if self.is_available(poll_id) else discord.Color.red(),
            timestamp=expires_at
        )
        embed.add_field(name=ctx._("vote.createdBy"), value=f"<@{poll['created_by']}>", inline=True)
        embed.add_field(name=ctx._("vote.id"), value=poll["vote_id"], inline=True)
        embed.set_footer(text=ctx._("vote.expires"))
        await ctx.send(embed=embed)

    @vote.command()
    @commands.guild_only()
    async def create(self, ctx, title, expires:int=24, *, description=""):
        """Creates a poll."""
        poll_id = self.generate_id()
        ctx.db.execute("INSERT INTO votes values (?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            poll_id,
            ctx.author.id,
            discord.utils.time_snowflake(datetime.datetime.utcnow()),
            expires,
            ctx.guild.id,
            title,
            description,
            "",""
        ))
        await ctx.say("vote.created", poll_id)

    @vote.command()
    @commands.guild_only()
    @is_poll_owner()
    async def delete(self, ctx, poll_id):
        """Deletes a poll you own."""
        # poll existance already checked
        ctx.db.execute("DELETE FROM votes WHERE vote_id = ?", (poll_id,))
        await ctx.say("vote.deleted")

    @vote.command()
    @is_poll_owner()
    async def results(self, ctx, poll_id):
        """Shows the result. Only open to poll owner."""
        poll = ctx.db.execute("SELECT * FROM votes WHERE vote_id = ?", (poll_id,)).fetchone()
        yes = len(poll["yes_users"]) and poll["yes_users"].count(",")
        no = len(poll["no_users"]) and poll["no_users"].count(",")
        embed = discord.Embed(
            title=ctx._("vote.pollResult", poll["title"]),
            color=discord.Color.green() if yes>=no else discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name=ctx._("vote.yes"), value=str(yes), inline=True)
        embed.add_field(name=ctx._("vote.no"), value=str(no), inline=True)
        await ctx.send(embed=embed)

    @vote.command()
    async def yes(self, ctx, poll_id):
        """Votes yes."""
        poll = ctx.db.execute("SELECT * FROM votes WHERE vote_id = ?", (poll_id,)).fetchone()
        if not poll:
            return await ctx.say("vote.pollNotFound")
        guild = self.bot.get_guild(poll["guild_id"])
        if ctx.author not in guild.members:
            return await ctx.say("vote.pollNotFound")
        if self.has_voted(poll_id, ctx.author.id):
            return await ctx.say("vote.alreadyVoted")
        if not self.is_available(poll_id):
            return await ctx.say("vote.pollExpired")
        yes_users = ",".join(map(str, poll["yes_users"].split(",") + [ctx.author.id]))
        ctx.db.execute("UPDATE votes SET yes_users = ? WHERE vote_id = ?", (yes_users, poll_id))
        await ctx.say("vote.voted")

    @vote.command()
    async def no(self, ctx, poll_id):
        """Votes no."""
        poll = ctx.db.execute("SELECT * FROM votes WHERE vote_id = ?", (poll_id,)).fetchone()
        if not poll:
            return await ctx.say("vote.pollNotFound")
        guild = self.bot.get_guild(poll["guild_id"])
        if ctx.author not in guild.members:
            return await ctx.say("vote.pollNotFound")
        if self.has_voted(poll_id, ctx.author.id):
            return await ctx.say("vote.alreadyVoted")
        if not self.is_available(poll_id):
            return await ctx.say("vote.pollExpired")
        no_users = ",".join(map(str, poll["no_users"].split(",") + [ctx.author.id]))
        ctx.db.execute("UPDATE votes SET no_users = ? WHERE vote_id = ?", (no_users, poll_id))
        await ctx.say("vote.voted")

def setup(bot):
    bot.add_cog(Vote(bot))
