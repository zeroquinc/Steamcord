from discord.ext import tasks, commands
from datetime import datetime
import asyncio

from src.steam.functions import get_all_achievements, create_and_send_embed, create_and_send_completion_embed
from config.globals import STEAM_API_KEY, ACHIEVEMENT_CHANNEL, PLATINUM_CHANNEL, STEAM_ID, INTERVAL_MINUTES
from utils.custom_logger import logger

class TasksCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.process_achievements.start()  # Always start the task when the cog is loaded
        self.completed_games = set()  # Initialize a set to track completed games

    @tasks.loop(minutes=INTERVAL_MINUTES)
    async def process_achievements(self):
        logger.info("Searching for Steam Achievements...")
        user_ids = STEAM_ID
        api_keys = STEAM_API_KEY
        channel = self.bot.get_channel(ACHIEVEMENT_CHANNEL)
        all_achievements = await get_all_achievements(user_ids, api_keys)
        all_achievements.sort(key=lambda a: (datetime.strptime(a[1].unlocktime, "%d/%m/%y %H:%M:%S"), a[4]/a[5]), reverse=True)
        logged_users = set()  # Set to keep track of users that have already been logged
        latest_unlocktimes = {}  # Dictionary to track the latest unlocktime for each user-game combination

        for game_achievement, user_achievement, user_game, user, total_achievements, current_count in all_achievements:
            if user.summary.personaname not in logged_users:
                logger.info(f"Found achievements for {user.summary.personaname}")
                logged_users.add(user.summary.personaname)
            await create_and_send_embed(channel, game_achievement, user_achievement, user_game, user, total_achievements, current_count)
            
            # Update the latest unlocktime
            completion_key = (user.summary.personaname, user_game.appid)
            latest_unlocktime = datetime.strptime(user_achievement.unlocktime, "%d/%m/%y %H:%M:%S")
            if completion_key not in latest_unlocktimes or latest_unlocktime > latest_unlocktimes[completion_key]:
                latest_unlocktimes[completion_key] = latest_unlocktime
            
            if current_count == total_achievements and completion_key not in self.completed_games:
                completion_channel = self.bot.get_channel(PLATINUM_CHANNEL)
                # Retrieve the latest unlocktime for this user-game combination
                latest_unlocktime = latest_unlocktimes[completion_key].strftime("%d/%m/%y %H:%M:%S")
                await create_and_send_completion_embed(completion_channel, user_game, user, total_achievements, latest_unlocktime)
                self.completed_games.add(completion_key)  # Mark this game as completed for this user
            await asyncio.sleep(1)

async def setup(bot):
    await bot.add_cog(TasksCog(bot))