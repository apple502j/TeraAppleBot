import datetime, asyncio
import discord
from discord.ext import commands, tasks
from .utils import Command

HOOK = "https://discordapp.com/api/webhooks/611117367866687509/lCoUWbPdX8cl7aIMriSwSmJCm5Q3a-loQeIVvs6YsjRm5CWDAowaUDnzGntrdb47YKA9"

class WW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        #self.send_loop.start()

    async def ww_(self, ctx, area):
        from_ = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        to = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        url = "http://api.aitc.jp/jmardb-api/search" \
        f"?datetime={from_}&datetime={to}&limit=1" \
        f"&title=気象特別警報・警報・注意報&order=new&areaname={area}"

        async with self.bot.session.get(url) as r:
            res = await r.json()
        try:
            data_url = res["data"][0]["link"]
        except IndexError:
            print(url)
            return discord.Embed(title="ww.notFound")
        timestamp = datetime.datetime.strptime(res["data"][0]["datetime"], "%Y-%m-%dT%H:%M:%S.000%z").astimezone(datetime.timezone.utc)
        async with self.bot.session.get(f"{data_url}.json") as r:
            res2 = (await r.json())["report"]
        embed = discord.Embed(
            title=ctx._("ww.fromApi", res2["head"]["title"], res2["control"]["editorialOffice"]),
            description=res2["head"]["headline"]["text"],
            timestamp=timestamp,
            color=discord.Color.red()
        )
        for item in res2["body"]["warning"][1]["item"]:
            embed.add_field(
                name=item["area"]["name"],
                value=", ".join([i["name"] for i in item["kind"]]),
                inline=True
            )
        embed.set_footer(
            text=ctx._("ww.footer"),
            icon_url="attachment://warning.png"
        )
        return embed

    @commands.command(id=2, cls=Command)
    @commands.cooldown(10, 20)
    async def ww(self, ctx, area):
        """Weather warnings."""
        emb=await self.ww_(ctx, area)
        await ctx.send(embed=embed, file=discord.File("warning.png"))

    #@tasks.loop(minutes=15)
    async def send_loop(self):
        class MockCTX:
            def __init__(selfa, **kwargs):
                selfa.__dict__.update(kwargs)
                selfa._=lambda key, *targs: self.bot._(key, discord.Object(398412979067944961), *targs)
                selfa.send = discord.Webhook.from_url(HOOK, adapter=discord.AsyncWebhookAdapter(self.bot.session)).send
                selfa.say = lambda *targs: selfa.send(selfa._(*targs))
        mocky=MockCTX()
        em=[]
        for pref in ("東京都", "神奈川県","静岡県", "長野県", "山梨県", "千葉県", "埼玉県", "群馬県", "栃木県", "茨城県"):
            emb=await self.ww_(mocky, pref)
            #await asyncio.sleep(10)
            print(type(emb))
            em.append(emb)
        await mocky.send(embeds=em)
        em=[]
        for pref in ("宮城県", "福島県", "新潟県", "岩手県"):
            emb=await self.ww_(mocky, pref)
            #await asyncio.sleep(10)
            print(type(emb))
            em.append(emb)
        await mocky.send(embeds=em)

    #@send_loop.before_loop
    async def bl(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(WW(bot))
