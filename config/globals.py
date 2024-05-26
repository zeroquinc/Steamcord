from dotenv import load_dotenv
import os

load_dotenv()

# Discord
DISCORD_SERVER_ID = os.getenv("DISCORD_SERVER_ID")
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]

# Steam
STEAM_API_KEY1 = os.getenv("STEAM_API_KEY1")
STEAM_API_KEY2 = os.getenv("STEAM_API_KEY2")
STEAM_API_URL = "https://api.steampowered.com"

# Tasks
ACHIEVEMENT_TIME = int(os.getenv("ACHIEVEMENT_TIME")) # The time in minutes to check for new achievements
ACHIEVEMENT_CHANNEL = int(os.getenv("ACHIEVEMENT_CHANNEL")) # The channel to send the achievements to