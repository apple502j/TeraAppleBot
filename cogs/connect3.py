import io, random, re, asyncio
from PIL import Image, ImageDraw
import discord
from discord.ext import commands

class Stone(discord.Enum):
    EMPTY = 0
    USER = 1
    CPU = 2

class Connect3(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.using = []
        self.board_regex = re.compile("^[0-2]-[0-2]$")

    def make_board_image(self, board):
        im = Image.open("connect3_default.png")
        im.load()
        draw = ImageDraw.Draw(im)
        for y in range(3):
            for x in range(3):
                if board[y][x] is Stone.USER:
                    draw.ellipse(
                        ((x*120+20, y*120+20), (x*120+100, y*120+100)),
                        fill=(0,0,0),
                        outline=(0,0,0)
                    )
                elif board[y][x] is Stone.CPU:
                    draw.rectangle(
                        ((x*120+20, y*120+20), (x*120+100, y*120+100)),
                        fill=(0,0,0),
                        outline=(0,0,0)
                    )
        file = io.BytesIO()
        im.save(file, "png")
        return file

    @staticmethod
    def can_place(board, x, y, *others):
        return board[y][x] is Stone.EMPTY

    def all_placeable(self, board):
        placeable = []
        for y in range(3):
            for x in range(3):
                if self.can_place(board, x, y):
                    placeable.append((x,y))
        return placeable

    @staticmethod
    def all_equal(to, *args):
        return args.count(to) == len(args)

    def connected_3(self, board, stone):
        return any([
            any([board[y]==[stone]*3 for y in range(3)]),
            any(self.all_equal(stone, board[0][x], board[1][x], board[2][x]) for x in range(3)),
            self.all_equal(stone, board[0][0], board[1][1], board[2][2]),
            self.all_equal(stone, board[2][0], board[1][1], board[0][2]),
        ])

    def nice_place(self, board, placeable):
        return random.choice(placeable)

        # the code below is no longer used: Game Theory matters
        for x, y in placeable:
            board[y][x]=Stone.CPU
            if self.connected_3(board, Stone.CPU):
                return x,y
            board[y][x]=Stone.USER
            if self.connected_3(board, Stone.USER):
                return x,y
            board[y][x]=Stone.EMPTY
        return random.choice(placeable)

    @commands.command()
    async def connect3(self, ctx):
        """Play Connect-3(Tic Tac Toe). You connect 3 stones.
        Circle is your stone. Rect is the bot's stone.
        You can only run one game at a time per channel.
        (i.e. do it on DM for if someone is playing)"""
        if ctx.channel.id in self.using:
            return await ctx.say("connect3.using")
        else:
            self.using.append(ctx.channel.id)
        board = [
            [Stone.EMPTY, Stone.EMPTY, Stone.EMPTY],
            [Stone.EMPTY, Stone.EMPTY, Stone.EMPTY],
            [Stone.EMPTY, Stone.EMPTY, Stone.EMPTY],
        ]
        board_msg = None
        while True:
            placeable = self.all_placeable(board)
            if self.connected_3(board, Stone.CPU) or not placeable:
                break
            if board_msg:
                await board_msg.delete()
            f=self.make_board_image(board)
            f.seek(0)
            board_msg = await ctx.send(embed=discord.Embed(
                title=ctx._("connect3.board"),
                description=ctx._("connect3.description"),
                color=random.randint(0, 0xFFFFFF)
            ).set_image(url="attachment://board.png"),file=discord.File(f, "board.png"))
            f.close()
            def user_input_check(msg):
                return all([
                    msg.author.id == ctx.author.id,
                    msg.channel.id == msg.channel.id,
                    len(msg.content)==3,
                    self.board_regex.match(msg.content)
                ]) and self.can_place(board, *map(int, msg.content.split("-")))
            try:
                user_input = await self.bot.wait_for("message", check=user_input_check, timeout=60)
            except asyncio.TimeoutError:
                await ctx.say("connect3.timeout")
                self.using.remove(ctx.channel.id)
                return
            user_x, user_y = [int(n) for n in user_input.content.split("-")]
            try:
                await user_input.delete()
            except discord.Forbidden:
                pass
            board[user_y][user_x] = Stone.USER
            placeable = self.all_placeable(board)
            if self.connected_3(board, Stone.USER) or not placeable:
                break
            cpu_x, cpu_y = self.nice_place(board.copy(), placeable)
            board[cpu_y][cpu_x] = Stone.CPU
        await board_msg.delete()
        f=self.make_board_image(board)
        f.seek(0)
        board_msg = await ctx.send(embed=discord.Embed(
            title=ctx._("connect3.board"),
            description=ctx._("connect3.description"),
            color=random.randint(0, 0xFFFFFF)
        ).set_image(url="attachment://board.png"),file=discord.File(f, "board.png"))
        f.close()
        self.using.remove(ctx.channel.id)
        if self.connected_3(board, Stone.CPU):
            return await ctx.say("connect3.cpuWon")
        elif self.connected_3(board, Stone.USER):
            return await ctx.say("connect3.userWon")
        else:
            return await ctx.say("connect3.tie")

def setup(bot):
    bot.add_cog(Connect3(bot))
