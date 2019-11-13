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
def setup(bot):
    pass
