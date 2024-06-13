from discord.ext import tasks, commands
from datetime import datetime
import asyncio

from src.steam.functions import get_all_achievements, create_and_send_embed
from config.globals import STEAM_API_KEY, ACHIEVEMENT_CHANNEL, STEAM_ID, INTERVAL_MINUTES
from utils.custom_logger import logger

class TasksCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.process_achievements.start()  # Always start the task when the cog is loaded

    @tasks.loop(minutes=INTERVAL_MINUTES)
    async def process_achievements(self):
        logger.info("Searching for Steam Achievements...")
        user_ids = STEAM_ID
        api_keys = STEAM_API_KEY
        channel = self.bot.get_channel(ACHIEVEMENT_CHANNEL)
        all_achievements = await get_all_achievements(user_ids, api_keys)
        # Sort all achievements by unlock time in descending order and then by order they were achieved in ascending order
        all_achievements.sort(key=lambda a: (datetime.strptime(a[1].unlocktime, "%d/%m/%y %H:%M:%S"), a[4]/a[5]), reverse=False)
        logged_users = set() # Set to keep track of users that have already been logged
        for game_achievement, user_achievement, user_game, user, total_achievements, current_count in all_achievements:
            if user.summary.personaname not in logged_users:
                logger.info(f"Found achievements for {user.summary.personaname}")
                logged_users.add(user.summary.personaname)
            await create_and_send_embed(channel, game_achievement, user_achievement, user_game, user, total_achievements, current_count)
            await asyncio.sleep(1)

async def setup(bot):
    await bot.add_cog(TasksCog(bot))