import discord
from discord.ext import commands
from datetime import datetime
import asyncio

from src.steam.functions import get_all_achievements, create_embed_description
from src.discord.embed import EmbedBuilder
from config.globals import STEAM_API_KEY1, STEAM_API_KEY2
from utils.custom_logger import logger

class DiscordBot:
    def __init__(self, token):
        intents = discord.Intents.default()
        intents.message_content = True

        self.token = token
        self.bot = commands.Bot(
            command_prefix="!",
            intents=intents
        )

        # Register event listeners
        self.bot.add_listener(self.on_ready)

    ## Start the bot
    async def start(self):
        try:
            await self.bot.start(self.token)
        except Exception as e:
            logger.error(f"Error starting the bot: {e}")

    ## Event listener for when the bot is ready
    async def on_ready(self):
        logger.info(
            f'Logged in as {self.bot.user.name} ({self.bot.user.id}) and is ready!'
        )
        
        @self.bot.command()
        async def steam(ctx):
            user_ids = [76561198035515815, 76561198840513734]
            api_keys = [STEAM_API_KEY1, STEAM_API_KEY2]

            all_achievements = await get_all_achievements(user_ids, api_keys)

            for game_achievement, user_achievement, user_game, user in all_achievements:
                description = create_embed_description(user_achievement, user_game)
                embed = EmbedBuilder(description=description)
                embed.set_thumbnail(url=game_achievement.icon)
                embed.set_footer(text=f"{user.summary.personaname} • {user_achievement.unlocktime}", icon_url=user.summary.avatarfull)
                await embed.send_embed(ctx.channel)
                await asyncio.sleep(1)