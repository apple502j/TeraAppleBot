import os
import sqlite3, pickle, json, bz2, logging
from discord.ext import commands
import aiohttp


LATEST_DB = 10
EXTENSIONS = [filename[:-3] for filename in os.listdir("./cogs") if filename.endswith(".py")]

with open("token.txt", "r", encoding="utf-8") as f:
    TOKEN = f.read().strip()

bot = commands.Bot(command_prefix='me:')
bot.load_extension("jishaku")
bot.session = aiohttp.ClientSession(
    headers={
        "User-Agent": "TeraAppleBot/apple502j; aiohttp on Python 3.7;"
    },
    skip_auto_headers=["User-Agent"],
    loop=bot.loop
)
bot.default_extensions = EXTENSIONS

sqlite3.register_converter('pickle', pickle.loads)
sqlite3.register_converter('json', json.loads)
sqlite3.register_adapter(dict, json.dumps)
sqlite3.register_adapter(list, pickle.dumps)

if not os.path.isfile('bot.db'):
    dbv = -1
else:
    dbv = None
dbw = sqlite3.connect('bot.db', detect_types=sqlite3.PARSE_DECLTYPES, isolation_level=None)
dbw.row_factory = sqlite3.Row
db = dbw.cursor()
dbv = dbv or db.execute('PRAGMA user_version').fetchone()[0]
if dbv < LATEST_DB:
    print("Migrating now...")
    for i in range(dbv + 1, LATEST_DB + 1):
        if not os.path.isfile(f'./migrate/v{i}.sql'):
            continue
        with open(f'./migrate/v{i}.sql') as f:
            db.executescript(f.read())
    db.execute('PRAGMA user_version = {}'.format(LATEST_DB))

bot.db = db

for extension in EXTENSIONS:
    bot.load_extension(f'cogs.{extension}')

@bot.event
async def on_message(msg):
    pass # handle at my cog

bot._on_ready_fired = False

@bot.event
async def on_ready():
    if not bot._on_ready_fired:
        bot.dispatch("ready_once")
        bot._on_ready_fired = True

_close = bot.close
async def close_handler():
    try:
        dbw.commit()
    except sqlite3.ProgrammingError:
        pass
    else:
        dbw.close()
    await bot.session.close()
    await _close()
bot.close = close_handler

bot.run(TOKEN)
