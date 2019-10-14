import discord
from discord.ext import commands
from PIL import ImageColor, Image
from .utils import Command

class Color(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(id=7, cls=Command)
    async def color(self, ctx, *, color = 'black'):
        """Returns a picture filled with a color. The argument can be:
        * hex value: 0xFFFFFF, #FFFFFF
        * hsv value: hsv(75, 100%, 80%)
        * raw value: 11450, f80
        * real name: black, red

        This uses ColourConverter and ImageColor.getrgb
        """
        try:
            real_color = (await commands.ColourConverter().convert(ctx, color)).to_rgb()
        except commands.BadArgument:
            try:
                real_color = ImageColor.getrgb(color)
            except ValueError:
                return await ctx.say("color.fail")
        im = Image.new('RGB', (400, 200), real_color)
        im.save('color_result.png')
        await ctx.send(embed=discord.Embed(
            title=ctx._("color.color", color)
        ).set_image(url="attachment://color.png"), file=discord.File("color_result.png", "color.png"))


def setup(bot):
    bot.add_cog(Color(bot))
