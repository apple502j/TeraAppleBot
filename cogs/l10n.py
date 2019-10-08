import os, json
from discord.ext import commands, tasks

SUPPORTED_LANGS = {"en"}

class LocalizedContext(commands.Context):
    def __init__(self, bot, message, *args, **kwargs):
        super().__init__(bot=bot, message=message, *args, **kwargs)
        self._ = lambda key, *targs: bot._(key, message.author, *targs)

class Localization(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        def store_user(user):
            if not self.bot.db.execute("SELECT user_id FROM users WHERE user_id = ?", (user.id,)).fetchone():
                print(f'DB: Stored user {user.id}')
                self.bot.db.execute("INSERT INTO users values (?,?)", (user.id, "en"))
        self.store_user = self.bot.store_user = store_user

        def translate_handler(text_id, user, *args):
            store_user(user)
            lang = self.bot.db.execute("SELECT lang FROM users WHERE user_id = ?", (user.id,)).fetchone()["lang"]
            return self.translations[lang].get(text_id, self.translations["en"][text_id]).format(*args)
        self._ = self.translate_handler = self.bot._ = translate_handler

        self.translations = {}
        for file in [i for i in os.listdir("./translations") if i.endswith(".json")]:
            with open(f'./translations/{file}', "r", encoding="utf-8") as f:
                self.translations[file[:-5]] = json.load(f)
        self.bot.translations = self.translations

    @commands.Cog.listener()
    async def on_ready(self):
        for user in self.bot.users:
            self.store_user(user)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        self.store_user(before)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        map(self.store_user, guild.members)

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return
        ctx = await self.bot.get_context(msg, cls=LocalizedContext)
        if ctx.valid:
            await self.bot.invoke(ctx)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.store_user(ctx.author)

    @tasks.loop(minutes=1)
    async def store_task(self):
        for user in self.bot.users:
            self.store_user(user)

    @commands.command()
    async def lang(self, ctx, lang=None):
        if lang and lang in SUPPORTED_LANGS:
            self.bot.db.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, ctx.author.id))
            await ctx.send(ctx._("lang.updated"))
        else:
            my_lang = self.bot.db.execute("SELECT lang FROM users WHERE user_id = ?", (ctx.author.id,)).fetchone()["lang"]
            await ctx.send(ctx._("lang.lang", my_lang))

def setup(bot):
    bot.add_cog(Localization(bot))
