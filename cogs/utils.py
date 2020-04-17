from datetime import timedelta, datetime
import discord
from discord.ext import commands

class Command(commands.Command):
    def __init__(self, *args, **kwargs):
        self.id = kwargs.pop('id')
        super().__init__(*args, **kwargs)

class Group(commands.Group):
    def __init__(self, *args, **kwargs):
        self.id = kwargs.pop('id')
        super().__init__(*args, **kwargs)

def perms(default=discord.Permissions.none(), **kwargs):
    p = discord.Permissions(default.value)
    p.update(**kwargs)
    return p
"""
def sort_members(guild):
    roles = reversed(tuple(filter(
        lambda role: role.hoist or role.is_default(),
        guild.roles
    )))
    members = []
    onlines = [m for m in guild.members if m.status is not discord.Status.offline]
    for role in roles:
        members += sorted(filter(lambda m: m not in members, onlines), key=lambda m: m.display_name)
    members += [m for m in guild.members if m not in members]
    return members
"""

def within(dt, minutes):
    return (datetime.utcnow() - dt) < timedelta(minutes=minutes)

class clean_mention(commands.Converter):
    def __init__(self, *, allow_by_perms=True):
        self.allow_by_perms=allow_by_perms

    async def convert(self, ctx, arg):
        arg="".join(l for l in arg if l.isprintable() or l == "\n")
        if ctx.guild is None:
            return arg
        perm = self.allow_by_perms and ctx.author.permissions_in(ctx.channel).mention_everyone
        def cleaner(text):
            needs_clean = False
            if (not perm) and '@everyone' in text:
                text = text.replace('@everyone', '')
                needs_clean = True
            if (not perm) and '@here' in text:
                text = text.replace('@here', '')
                needs_clean = True
            for role in ctx.guild.roles:
                if role.mentionable:
                    continue
                if (not perm) and f'<@&{role.id}>' in text:
                    text = text.replace(f'<@&{role.id}>', '')
                    needs_clean = True
            return needs_clean, text
        should_clean, arg = cleaner(arg)
        while should_clean:
            should_clean, arg = cleaner(arg)
        return arg


def range_num(array, num):
    for i in range(len(array)):
        if num <= array[i]:
            return i

def setup(bot):
    pass
