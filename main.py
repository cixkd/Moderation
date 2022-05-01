from disnake import Intents
from disnake.ext import commands
import os, traceback
import asyncpg

from config import Token, Database
from assets import functions as func

intents = Intents.default()
intents.members = True

bot = commands.Bot(case_insensitive=True, command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print('*********\nBot is Ready.\n*********')
    

bot.remove_command('help')

async def DbPool():
    # import ssl
    # ssl_object = ssl.create_default_context()
    # ssl_object.check_hostname = False
    # ssl_object.verify_mode = ssl.CERT_NONE
    bot.db = await asyncpg.create_pool(
        host=Database['host'],
        port=Database['port'],
        user=Database['user'],
        password=Database['password'],
        database=Database['database']
        # , ssl=ssl_object
        )
    print("Connected to The Database.")

bot.loop.run_until_complete(DbPool())

@bot.command()
async def ping(ctx):
    await ctx.send (f"📶 {round(bot.latency * 1000)}ms")

@bot.event
async def on_command_error(ctx,error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=func.ErrorEmbed('Error', 'You do not have the correct permissions required to run this command.'))
    if isinstance(error, (commands.CommandNotFound, commands.CheckFailure)):
        return

for file in os.listdir('./cogs'):
    if file.endswith('.py') and file != '__init__.py':
        try:
            bot.load_extension("cogs."+file[:-3])
            print(f"{file[:-3]} Loaded successfully.")
        except:
            print(f"Unable to load {file[:-3]}.")
            print(traceback.format_exc())

bot.run(Token)
