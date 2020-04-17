from datetime import timedelta, datetime
import asyncio
import discord
from discord.ext import commands
from .utils import Command, Group

STAR_EMOJI = "\U00002b50"
TOPIC = "Starboard by {mention}. Threshold: {threshold} / Max Age: {age} days"

class FakeContext(object):
    def __init__(self, guild):
        self.guild = guild

    def _(self, *args, **kwargs):
        pass

class StarError(commands.CheckFailure):
    pass

class Star(commands.Converter):
    async def convert(self, ctx, arg):
        star_cog = ctx.bot.get_cog("Stars")
        try:
            star_cog.starboard_available(ctx)
        except (NoPrivateMessage, StarError):
            raise commands.BadArgument("Star parsing failed.", arg)
        star_obj = ctx.bot.db.execute(
            "SELECT * FROM starboard_items " \
            "WHERE visible = 1 AND (item_id = ? OR original_id = ?)",
            (arg,arg)
        ).fetchone()
        if star_obj:
            return star_obj
        else:
            raise commands.BadArgument("Star parsing failed.", arg)

class Stars(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def starboard_available(self, ctx, check_availability=True):
        """
        Context can be a object which has:
        - guild
        - _ (translation)
        """
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        board = self.bot.db.execute("SELECT starboard_id FROM guilds WHERE guild_id = ?", (ctx.guild.id,)).fetchone()
        if not board:
            raise StarError(ctx._("star.notAvailable"))
        board_id = board["starboard_id"]
        board_item = self.bot.db.execute("SELECT * FROM starboards WHERE starboard_id = ?", (board_id,)).fetchone()
        if board_item["enabled"] != 1 and check_availability:
            raise StarError(ctx._("star.notAvailable"))
        ch = ctx.guild.get_channel(board_item["channel_id"])
        if not ch:
            self.destroy_starboard(board_item["channel_id"], ctx.guild.id)
            raise StarError(ctx._("star.notAvailable"))
        perms = ch.permissions_for(ctx.guild.me)
        if not all([
            perms.read_messages,
            perms.send_messages,
            perms.add_reactions,
            perms.manage_messages,
            perms.embed_links,
            perms.attach_files,
            perms.read_message_history
        ]):
            raise StarError(ctx._("star.permission"))
        return True

    async def cog_check(self, ctx):
        if ctx.command.name in ("starboard", "help", "dm"):
            return True
        else:
            return self.starboard_available(ctx, check_availability = (ctx.command.name != "enable"))

    async def destroy_item(self, channel_id, item_id):
        try:
            await self.bot.http.delete_message(channel_id, item_id)
        except discord.HTTPException:
            pass
        self.bot.db.execute("DELETE FROM starboard_items WHERE item_id = ?", (item_id,))

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        self.destroy_starboard(channel.id, channel.guild.id)

    def destroy_starboard(self, channel_id, guild_id):
        board_item = self.bot.db.execute("SELECT * FROM starboards WHERE channel_id = ?", (channel_id,)).fetchone()
        if not board_item:
            return
        self.bot.db.execute("UPDATE guilds SET starboard_id = 0 WHERE guild_id = ?", (guild_id,))
        self.bot.db.execute("DELETE FROM starboards WHERE channel_id = ?", (channel_id,))
        self.bot.db.execute("DELETE FROM starboard_items WHERE channel_id = ?", (channel_id,))

    def get_star_reaction(self, msg):
        return discord.utils.find(lambda r: str(r.emoji) == STAR_EMOJI, msg.reactions)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        These are the checks done, in order:
        - ignore any non-stars
        - ignore bots
        - ignore banneds
        - ignore conditions where starboard is not available, including:
        -- DM
        -- starboard not registered
        -- starboard disabled
        -- starboard deleted (this destroys starboard)
        -- starboard missing permission
        - ignore message being deleted on starboard channel
        - ignore webhook messages
        - ignore star by the author
        - ignore old messages
        - ignore "too-few-to-handle" case
        - ignore embed-only messages
        - ignore system messages
        - ignore NSFW channels

        the "double star" case is handled in actual_star_count.
        """
        if str(payload.emoji) != STAR_EMOJI:
            return
        if self.bot.get_user(payload.user_id).bot:
            return
        if getattr(self.bot, "is_banned", None) and await self.bot.is_banned(payload.user_id):
            return
        guild = self.bot.get_guild(payload.guild_id)
        ctx = FakeContext(guild)
        try:
            assert self.starboard_available(ctx)
        except:
            return
        else:
            board = self.bot.db.execute("SELECT starboard_id FROM guilds WHERE guild_id = ?", (guild.id,)).fetchone()
            board_item = self.bot.db.execute("SELECT * FROM starboards WHERE starboard_id = ?", (board["starboard_id"],)).fetchone()
            if board_item["channel_id"] == payload.channel_id:
                real = self.bot.db.execute("SELECT * FROM starboard_items WHERE item_id = ?",(payload.message_id,)).fetchone()
                try:
                    msg = await guild.get_channel(real["channel_id"]).fetch_message(real["original_id"])
                except discord.NotFound:
                    return await self.destroy_item(payload.channel_id, payload.message_id)
            else:
                msg = await guild.get_channel(payload.channel_id).fetch_message(payload.message_id)
            # msg is original, no matter where the star is placed
            if msg.webhook_id:
                return
            if payload.user_id == msg.author.id:
                return
            if msg.created_at + timedelta(days=board_item["age"]) < datetime.utcnow():
                return
            if self.get_star_reaction(msg).count < board_item["threshold"]:
                return
            if not msg.content:
                return
            if msg.type is not discord.MessageType.default:
                return
            if msg.channel.is_nsfw():
                return
            await self.add_star(msg)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if str(payload.emoji) != STAR_EMOJI:
            return
        if self.bot.get_user(payload.user_id).bot:
            return
        if getattr(self.bot, "is_banned", None) and await self.bot.is_banned(payload.user_id):
            return
        guild = self.bot.get_guild(payload.guild_id)
        ctx = FakeContext(guild)
        try:
            assert self.starboard_available(ctx)
        except:
            return
        else:
            board = self.bot.db.execute("SELECT starboard_id FROM guilds WHERE guild_id = ?", (guild.id,)).fetchone()
            board_item = self.bot.db.execute("SELECT * FROM starboards WHERE starboard_id = ?", (board["starboard_id"],)).fetchone()
            if board_item["channel_id"] == payload.channel_id:
                real = self.bot.db.execute("SELECT * FROM starboard_items WHERE item_id = ?",(payload.message_id,)).fetchone()
                try:
                    msg = await guild.get_channel(real["channel_id"]).fetch_message(real["original_id"])
                except discord.NotFound:
                    return await self.destroy_item(payload.channel_id, payload.message_id)
            else:
                msg = await guild.get_channel(payload.channel_id).fetch_message(payload.message_id)
            # msg is original, no matter where the star is placed
            if msg.webhook_id:
                return
            if payload.user_id == msg.author.id:
                return
            if msg.created_at + timedelta(days=board_item["age"]) < datetime.utcnow():
                return
            if not msg.content:
                return
            if msg.type is not discord.MessageType.default:
                return
            if msg.channel.is_nsfw():
                return
            await self.remove_star(msg)

    async def actual_star_count(self, msg):
        reacts = self.get_star_reaction(msg)
        if reacts:
            original_users = await reacts.users().flatten()
            if msg.author in original_users:
                original_users.remove(msg.author)
            original_users = [user for user in original_users if not user.bot]
        else:
            original_users = []
        item = self.bot.db.execute("SELECT * FROM starboard_items WHERE original_id = ?",(msg.id,)).fetchone()
        if item:
            board = self.bot.db.execute("SELECT * FROM starboards WHERE starboard_id = ?",(item["starboard_id"],)).fetchone()
            try:
                board_msg = await self.bot.get_channel(board["channel_id"]).fetch_message(item["item_id"])
            except discord.NotFound:
                await self.destroy_item(board["channel_id"], item["item_id"])
                raise StarError()
            else:
                reacts = self.get_star_reaction(board_msg)
                if reacts:
                    board_users = await reacts.users().flatten()
                    if msg.author in board_users:
                        board_users.remove(msg.author)
                    board_users = [user for user in board_users if not user.bot]
                else:
                    board_users = []
                return len(set(original_users) | set(board_users))
        return len(original_users)

    def prepare_message(self, msg, count):
        content = f"{STAR_EMOJI} **{count}** \U0001f194: {msg.id}"
        embed = discord.Embed(
            title="See Original", # this can't be localized - sadly.
            description=f"{msg.channel.mention} [Link]({msg.jump_url})",
            colour=0xeeee30,
            timestamp=msg.created_at
        ).add_field(name="Content", value=msg.content, inline=True)
        embed.set_author(name=msg.author.display_name, icon_url=str(msg.author.avatar_url))
        return content, embed

    async def add_star(self, msg):
        try:
            count = await self.actual_star_count(msg)
        except StarError:
            return
        board = self.bot.db.execute("SELECT * FROM starboards WHERE guild_id = ?", (msg.guild.id,)).fetchone()
        item = self.bot.db.execute("SELECT * FROM starboard_items WHERE original_id = ?",(msg.id,)).fetchone()
        if count < board["threshold"]:
            return
        content, embed = self.prepare_message(msg, count)
        if item:
            await self.bot.http.edit_message(
                board["channel_id"],
                item["item_id"],
                **{
                    "content": content,
                    "embed": embed.to_dict()
                }
            )
            self.bot.db.execute("UPDATE starboard_items SET visible = 1 WHERE original_id = ?", (msg.id,))
        else:
            channel = self.bot.get_channel(board["channel_id"])
            board_msg = await channel.send(content, embed=embed)
            self.bot.db.execute("INSERT INTO starboard_items values (?,?,?,?,?,?,?)", (
                board_msg.id,
                msg.id,
                msg.guild.id,
                msg.channel.id,
                msg.author.id,
                board["starboard_id"],
                1
            ))
            dm = self.bot.db.execute("SELECT starboard_dm FROM users WHERE user_id = ?",(msg.author.id,)).fetchone()
            if dm and dm["starboard_dm"]:
                await msg.author.send(self.bot._("star.dm", msg.author, msg.guild.name, board_msg.jump_url))

    async def remove_star(self, msg):
        try:
            count = await self.actual_star_count(msg)
        except StarError:
            return
        board = self.bot.db.execute("SELECT * FROM starboards WHERE guild_id = ?", (msg.guild.id,)).fetchone()
        item = self.bot.db.execute("SELECT * FROM starboard_items WHERE original_id = ?",(msg.id,)).fetchone()
        if not item:
            return # why do you care a case where the star was never starboarded? idk

        if count < board["threshold"]:
            await self.bot.http.edit_message(
                board["channel_id"],
                item["item_id"],
                **{
                    "content": "\u200b",
                    "embed": None
                }
            )
            self.bot.db.execute("UPDATE starboard_items SET visible = 0 WHERE original_id = ?", (msg.id,))
        else:
            content, embed = self.prepare_message(msg, count)
            channel = self.bot.get_channel(board["channel_id"])
            await self.bot.http.edit_message(
                board["channel_id"],
                item["item_id"],
                **{
                    "content": content,
                    "embed": embed.to_dict()
                }
            )

    async def set_topic(self, channel_id):
        board = self.bot.db.execute("SELECT * FROM starboards WHERE channel_id = ?", (channel_id,)).fetchone()
        if (not board) or not board["enabled"]:
            return # should not happen but
        ch = self.bot.get_channel(channel_id)
        await ch.edit(topic=TOPIC.format(
            mention=self.bot.user.mention,
            threshold=board["threshold"],
            age=board["age"])
        )

    @commands.command(id=22, cls=Command)
    @commands.guild_only()
    @commands.has_permissions(
        add_reactions=True,
        manage_messages=True,
        embed_links=True,
        attach_files=True,
        read_message_history=True,
        manage_roles=True,
        manage_channels=True,
    )
    @commands.bot_has_permissions(
        # basic permissions
        read_messages=True,
        send_messages=True,
        add_reactions=True,
        manage_messages=True,
        embed_links=True,
        attach_files=True,
        read_message_history=True,
        # creation specific permissions
        manage_roles=True,
        manage_channels=True
    )
    async def starboard(self, ctx):
        """
        Creates a starboard. A starboard is a channel which has messages with some stars.
        To configure this starboard (such as max age and threshold, which are 7 days and
        5 stars by default), use starconfig's subcommands. See the help for details.

        To use starboard, add a star. Note that only :star: works, not other stars. You
        can add the star to both original and starboard messages. **Note that a secret
        channel's messages can be on the starboard depending on threshold and star counts.**

        This command requires Read Message, Send Message, Add Reactions, Manage Messages,
        Embed Links, Attach Files, Read Message History, Manage Roles and Manage Channels
        permissions for both you and me. All permissions listed above, except for the last 2
        ones, are required by the bot to use starboard feature.

        These are some reasons on why it doesn't pick up the star:
        - Wrong emojis
        - Bot reactions
        - Conditions where starboard is not available, including:
        -- starboard disabled
        -- starboard deleted or unstarboarded
        -- starboard missing permission
        - Message is deleted on starboard channel
        - Webhook messages
        - Star by author
        - Old (see maxage)
        - Embed-only or Attachments-only
        - System messages (such as Join)
        - NSFW channels' messages
        - Bot was down

        To disable the entire star system, lock starboard and starconfig (if a starboard was previously
        created).
        """
        if self.bot.db.execute("SELECT * FROM starboards WHERE guild_id = ?",(ctx.guild.id,)).fetchone():
            return await ctx.say("star.already")
        async with ctx.typing():
            await ctx.channel.edit(
                topic=TOPIC.format(mention=self.bot.user.mention, threshold=5, age=7), # yeah can't be localized
                nsfw=False,
                reason="Starboard preparation"
            )
            await ctx.channel.set_permissions(ctx.guild.me,
                read_messages=True,
                send_messages=True,
                add_reactions=True,
                manage_messages=True,
                embed_links=True,
                attach_files=True,
                read_message_history=True,
                manage_roles=True,
                manage_channels=True
            )
            await ctx.channel.set_permissions(ctx.guild.default_role,
                read_messages=True,
                send_messages=False,
                add_reactions=True,
                read_message_history=True
            )
            tutorial = await ctx.say("star.done", STAR_EMOJI)
            try:
                await tutorial.pin()
            except discord.HTTPException:
                pass
        self.bot.db.execute("INSERT INTO starboards(guild_id, channel_id,threshold,age,enabled) VALUES (?, ?,5,7,1)", (ctx.guild.id, ctx.channel.id))
        starboard_id = self.bot.db.execute("SELECT starboard_id FROM starboards WHERE channel_id = ?", (ctx.channel.id,)).fetchone()["starboard_id"]
        self.bot.db.execute("UPDATE guilds SET starboard_id = ? WHERE guild_id = ?", (starboard_id, ctx.guild.id))

    @commands.command(id=23, cls=Command)
    @commands.has_permissions(manage_channels=True)
    async def unstarboard(self, ctx):
        """Destroys the starboard. For usual uses, use me:starconfig disable instead."""
        if not self.bot.db.execute("SELECT * FROM starboards WHERE channel_id = ?",(ctx.channel.id,)).fetchone():
            return await ctx.say("star.notStarboard")
        await ctx.say("star.timeout")
        try:
            await self.bot.wait_for("message", check=lambda msg: msg.channel == ctx.channel and msg.author == ctx.author, timeout=10)
        except asyncio.TimeoutError:
            self.destroy_starboard(ctx.channel.id, ctx.guild.id)
            await ctx.say("star.unstarboarded")
        else:
            await ctx.say("star.kept")

    @commands.group(invoke_without_command=True,id=24, cls=Group)
    @commands.has_permissions(manage_channels=True)
    async def starconfig(self, ctx):
        pass

    @starconfig.command(id=25, cls=Command)
    @commands.has_permissions(manage_channels=True)
    async def enable(self, ctx):
        """Enables a disabled starboard."""
        self.bot.db.execute("UPDATE starboards SET enabled = 1 WHERE channel_id = ?", (ctx.channel.id,))
        await ctx.say("star.enabled")

    @starconfig.command(id=26, cls=Command)
    @commands.has_permissions(manage_channels=True)
    async def disable(self, ctx):
        """Disables a starboard."""
        self.bot.db.execute("UPDATE starboards SET enabled = 0 WHERE channel_id = ?", (ctx.channel.id,))
        await ctx.say("star.disabled")

    @starconfig.command(id=27, cls=Command)
    @commands.has_permissions(manage_channels=True)
    async def maxage(self, ctx, age: int):
        """
        Sets "max age" for the starboard messages. If a message is older than the specified days,
        the message is ignored. Note that existing messages are not affected. Defaults to 7 (one week).
        """
        if age > 0:
            self.bot.db.execute("UPDATE starboards SET age = ? WHERE channel_id = ?", (age,ctx.channel.id))
            await ctx.say("star.age", age)
            await self.set_topic(ctx.channel.id)
        else:
            await ctx.say("star.unsigned", age)

    @starconfig.command(id=28, cls=Command)
    @commands.has_permissions(manage_channels=True)
    async def threshold(self, ctx, threshold: int):
        """
        Sets "threshold" for the starboard messages. The specified number of stars are required to
        put the message on the starboard. Note that existing messages are not affected. Defaults to 5.
        """
        if threshold > 0:
            self.bot.db.execute("UPDATE starboards SET threshold = ? WHERE channel_id = ?", (threshold, ctx.channel.id))
            await ctx.say("star.threshold", threshold)
            await self.set_topic(ctx.channel.id)
        else:
            await ctx.say("star.unsigned", threshold)

    @commands.group(id=29, cls=Group)
    async def star(self, ctx):
        pass

    @star.command(name="show", id=30, cls=Command)
    async def star_show(self, ctx, item: Star):
        """Shows a starboard item. The argument can be either original message ID or starboard item ID."""
        board = self.bot.db.execute("SELECT * FROM starboards WHERE guild_id = ?", (ctx.guild.id,)).fetchone()
        try:
            board_msg = await self.bot.get_channel(board["channel_id"]).fetch_message(item["item_id"])
        except discord.NotFound:
            return await self.destroy_item(board["channel_id"], item["item_id"])
        else:
            await ctx.send(board_msg.content, embed=board_msg.embeds[0])

    @star.command(name="random", id=31, cls=Command)
    async def star_random(self, ctx):
        """Shows a random item."""
        board = self.bot.db.execute("SELECT * FROM starboards WHERE guild_id = ?", (ctx.guild.id,)).fetchone()
        item = self.bot.db.execute(
            "SELECT item_id FROM starboard_items WHERE visible = 1 " \
            "ORDER BY random() LIMIT 1"
        ).fetchone()
        if not item:
            return
        try:
            board_msg = await self.bot.get_channel(board["channel_id"]).fetch_message(item["item_id"])
        except discord.NotFound:
            return await self.destroy_item(board["channel_id"], item["item_id"])
        else:
            await ctx.send(board_msg.content, embed=board_msg.embeds[0])

    @star.command(name="dm", id=33, cls=Command)
    async def star_dm(self, ctx, enable: bool = None):
        """
        Enables/disables DM when your message was stared.
        If the parameter is not given, this returns current status.
        Can be used anywhere including DM.
        """
        if enable is None:
            result = self.bot.db.execute("SELECT starboard_dm FROM users WHERE user_id = ?", (ctx.author.id,)).fetchone()
            enabled = result["starboard_dm"] if result else 0
            status_str = ctx._(f"star.dm{['Disabled', 'Enabled'][enabled]}")
            return await ctx.say("star.dmCurrent", status_str)
        self.bot.db.execute("UPDATE users SET starboard_dm = ? WHERE user_id = ?",(
            int(enable),
            ctx.author.id
        ))
        status_str = ctx._(f"star.dm{['Disabled', 'Enabled'][enable]}")
        return await ctx.say("star.dmCurrent", status_str)

def setup(bot):
    bot.add_cog(Stars(bot))
