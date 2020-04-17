import json
import asyncio
import math
from datetime import datetime
from random import uniform
import discord
from discord.ext import commands
from .utils import Command, range_num

class Fishing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("fishing_loot.json", "r", encoding="utf-8") as f:
            self.loot = json.load(f)
        self.fish_category_chance = self.get_chance([cat["chance"] for cat in self.loot])
        self.fish_chance_dic = [
            self.get_chance([item["chance"] for item in cat["results"]])
            for cat in self.loot
        ]

    def get_chance(self, nums):
        return [sum(nums[:c+1]) for c in range(len(nums))]

    def get_fish(self):
        r = uniform(0, self.fish_category_chance[-1])
        category_num = range_num(self.fish_category_chance, r)
        cat = self.loot[category_num]
        r2 = uniform(0, self.fish_chance_dic[category_num][-1])
        fish_num = range_num(self.fish_chance_dic[category_num], r2)
        item = cat["results"][fish_num]
        return category_num, fish_num

    def get_damage(self, item):
        if item.get("durability", None):
            d=item["durability"]
            if item.get("damage", None):
                d*=uniform(*item["damage"])
            return math.ceil(d)
        else:
            return None

    @commands.command(id=38, cls=Command)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def fish(self, ctx):
        """Fishing is fun!"""
        await ctx.say("fish.fishing")
        await asyncio.sleep(uniform(1, 10))
        c_num, i_num = self.get_fish()
        cat = self.loot[c_num]
        item = cat["results"][i_num]
        embed = discord.Embed(
            title=ctx._(cat["name"]),
            timestamp=datetime.utcnow()
        ).add_field(
            name=item["emoji"],
            value=ctx._(item["name"])
        )
        damage = self.get_damage(item)
        if damage:
            embed.set_footer(text=ctx._("fish.damaged", damage, item["durability"]))
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Fishing(bot))
