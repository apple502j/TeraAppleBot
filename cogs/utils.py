from discord.ext import commands

class Command(commands.Command):
    def __init__(self, *args, **kwargs):
        self.id = kwargs.pop('id')
        super().__init__(*args, **kwargs)

class Group(commands.Group):
    def __init__(self, *args, **kwargs):
        self.id = kwargs.pop('id')
        super().__init__(*args, **kwargs)

def setup(bot):
    pass
