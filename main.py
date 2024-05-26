import asyncio

from src.discord.bot import DiscordBot

from config.globals import DISCORD_TOKEN

async def main():
    discord_bot = DiscordBot(DISCORD_TOKEN)

    await asyncio.gather(
        discord_bot.start()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by keyboard interrupt.")