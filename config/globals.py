from dotenv import load_dotenv
import os

load_dotenv()

# Discord
DISCORD_SERVER_ID = os.getenv("DISCORD_SERVER_ID")
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]

# Steam
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_API_URL = "https://api.steampowered.com"