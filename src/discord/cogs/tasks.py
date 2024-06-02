import asyncio
from discord.ext import tasks, commands
from datetime import datetime

from src.discord.embed import EmbedBuilder
from src.steam.functions import get_all_achievements, create_embed_description_footer
from config.globals import STEAM_API_KEY1, STEAM_API_KEY2, ACHIEVEMENT_CHANNEL
from utils.custom_logger import logger

class TasksCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.process_achievements.start()  # Always start the task when the cog is loaded

    @tasks.loop(minutes=60)
    async def process_achievements(self):
        logger.info("Start Achievement task")

        user_ids = [76561198035515815, 76561198840513734]
        api_keys = [STEAM_API_KEY1, STEAM_API_KEY2]
        channel = self.bot.get_channel(ACHIEVEMENT_CHANNEL)

        all_achievements = await get_all_achievements(user_ids, api_keys)

        # Sort all achievements by unlock time in descending order
        all_achievements.sort(key=lambda a: datetime.strptime(a[1].unlocktime, "%d/%m/%y %H:%M:%S"), reverse=False)

        if all_achievements:
            logger.info("Found achievements")
        else:
            logger.info("No achievements found")

        for game_achievement, user_achievement, user_game, user, total_achievements, current_count in all_achievements:
            description, footer = create_embed_description_footer(user_achievement, user_game, current_count, total_achievements)
            embed = EmbedBuilder(description=description)
            embed.set_thumbnail(url=game_achievement.icon)
            embed.set_footer(text=footer, icon_url=user.summary.avatarfull)
            await embed.send_embed(channel)
            await asyncio.sleep(1)

async def setup(bot):
    await bot.add_cog(TasksCog(bot))