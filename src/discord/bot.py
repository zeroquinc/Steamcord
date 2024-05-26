import discord
from discord.ext import commands
from datetime import datetime
import asyncio

from src.steam.functions import get_achievement_description
from src.discord.embed import EmbedBuilder
from src.steam.functions import check_recently_played_games
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

            all_achievements = []
            for user_id, api_key in zip(user_ids, api_keys):
                achievements = await check_recently_played_games(user_id, api_key)
                all_achievements.extend(achievements)

            # Sort achievements by unlocktime of the corresponding user_achievement
            all_achievements.sort(key=lambda pair: datetime.strptime(pair[1].unlocktime, '%d/%m/%y %H:%M:%S'))

            # Add achievements to the embed
            for game_achievement, user_achievement, user_game, user in all_achievements:
                # Use the game achievement in the description
                achievement_info = get_achievement_description(user_game.appid, user_achievement.name)
                if achievement_info:
                    description = f"**{user_achievement.name}** <:silver:1242467048035192955> **{achievement_info['percentage']}**\n{achievement_info['description']}\n\n[{user_game.name}]({user_game.url})"
                else:
                    description = f"**{user_achievement.name}**\n\n{user_game.name}"
                embed = EmbedBuilder(description=description)
                embed.set_thumbnail(url=game_achievement.icon)
                embed.set_footer(text=f"{user.summary.personaname} • {user_achievement.unlocktime}", icon_url=user.summary.avatarfull)
                # Send the embed
                await embed.send_embed(ctx.channel)
                await asyncio.sleep(1)