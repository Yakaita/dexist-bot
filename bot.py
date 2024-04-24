from discord.ext import commands
from dotenv import load_dotenv
import discord, os, json

#load the .env file
load_dotenv()
#load the config
with open('config.json','r') as config_file: config = json.load(config_file)

# setup bot
bot = commands.Bot(command_prefix=config["commandPrefix"], intents=discord.Intents.all())

# On ready event
@bot.event
async def on_ready():
    if config["sendOnReadyMessage"]: await bot.get_channel(config["onReadyMessageChannelId"]).send("Ready to shiny hunt!")

bot.run(os.getenv("BOT_TOKEN"))