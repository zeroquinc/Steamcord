import discord
from discord.ext import commands
import asyncio

from config.globals import ENABLE_DELAY
from utils.datetime import DateUtils
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

        # Wait until the next 00th minute and load tasks
        await self.load_tasks_at_next_hour()

    ## Load tasks at the next 00th minute
    async def load_tasks_at_next_hour(self):
        if ENABLE_DELAY:
            # Calculate seconds until the next 00th minute
            seconds_until_next_hour = DateUtils.seconds_until_next_hour()
            # Calculate minutes and seconds until the next 00th minute
            minutes_until_next_hour, seconds_remaining = divmod(seconds_until_next_hour, 60)
            # Print the minutes and seconds until the next 00th minute
            logger.info(f'Waiting for {minutes_until_next_hour} minutes and {seconds_remaining} seconds before starting task...')
            # Wait until the next 00th minute
            await asyncio.sleep(seconds_until_next_hour)

        # Load the tasks cog
        logger.info('Loading tasks cog')
        await self.bot.load_extension('src.discord.cogs.tasks')