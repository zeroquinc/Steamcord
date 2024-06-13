from dotenv import load_dotenv
import os

load_dotenv()

# Discord
DISCORD_SERVER_ID = os.getenv("DISCORD_SERVER_ID")
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]

# Steam
STEAM_API_KEY = (os.getenv("STEAM_API_KEY") or "").split(',')
STEAM_ID = (os.getenv("STEAM_ID") or "").split(',')
STEAM_API_URL = "https://api.steampowered.com"

# Tasks
ACHIEVEMENT_TIME = int(os.getenv("ACHIEVEMENT_TIME")) # The time in minutes to check for new achievements
ACHIEVEMENT_CHANNEL = int(os.getenv("ACHIEVEMENT_CHANNEL")) # The channel to send the achievements to
INTERVAL_MINUTES = int(os.getenv("INTERVAL_MINUTES")) # The interval in minutes to check for new achievements

# Delay
ENABLE_DELAY = os.getenv("ENABLE_DELAY") == "True"