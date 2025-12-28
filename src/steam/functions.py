from datetime import datetime, timedelta

import discord
from api.client import SteamClient
from config.globals import ACHIEVEMENT_TIME, PLATINUM_ICON
from src.discord.embed import EmbedBuilder
from utils.image import get_discord_color
from utils.datetime import DateUtils
from utils.custom_logger import logger

DATE_FORMAT = '%d/%m/%y %H:%M:%S'

# Scraping from steamhunters has been removed (site now blocks scraping).
# The data-dependent helpers were deleted. Keep a small store for runtime counts.
user_current_counts = {}

async def get_user_games(user_id, api_key):
    client = SteamClient(api_key)
    user = client.user(user_id)
    user.get_user_summaries()
    user.get_owned_games()
    return user

async def get_recently_played_games(user):
    current_time = datetime.now().strftime(DATE_FORMAT)
    recently_played_games = []

    # Prefer owned games list first (contains last_played timestamps when available)
    for user_game in getattr(user, 'owned_games', []):
        if user_game.last_played != "Unknown":
            try:
                last_played_date = datetime.strptime(user_game.last_played, DATE_FORMAT)
                if datetime.strptime(current_time, DATE_FORMAT) - last_played_date <= timedelta(minutes=ACHIEVEMENT_TIME):
                    recently_played_games.append(user_game)
            except Exception:
                # If parsing fails, skip and continue
                continue

    # Also include results from the recently-played endpoint (covers family-shared games)
    try:
        if hasattr(user, 'get_recently_played_games'):
            user.get_recently_played_games()
            for rp in getattr(user, 'recently_played_games', []):
                # avoid duplicates by appid
                if rp.appid not in [g.appid for g in recently_played_games]:
                    recently_played_games.append(rp)
    except Exception as e:
        logger.debug(f"Could not fetch recently played games for {getattr(user, 'steam_id', 'unknown')}: {e}")

    return recently_played_games

async def get_game_achievements(user_game, user, client):
    game_instance = client.game()
    try:
        game_instance.get_game_achievements(user_game.appid)
    except Exception as e:
        logger.error(f"Error processing achievements for game {user_game.appid}: {e}")
        return None

    # fetch the user's achievements for this game (synchronous API)
    try:
        user.get_user_achievements(user_game.appid)
    except Exception as e:
        logger.error(f"Error fetching user achievements for {user.summary and getattr(user.summary, 'personaname', user.steam_id)}: {e}")
        return None

    if not game_instance.achievements:
        return None

    total_achievements = len(game_instance.achievements)
    return game_instance.achievements, user.achievements, total_achievements

async def find_matching_achievements(user_achievement, game_achievements, current_time, user_game, user):
    matching_achievements = []
    for game_achievement in game_achievements:
        if game_achievement.displayname == user_achievement.name:
            unlocktime = datetime.strptime(user_achievement.unlocktime, DATE_FORMAT)
            if unlocktime and datetime.strptime(current_time, DATE_FORMAT) - unlocktime <= timedelta(minutes=ACHIEVEMENT_TIME):
                matching_achievements.append((game_achievement, user_achievement, user_game, user))
    return matching_achievements

def calculate_completion_time_span(data):
    # Check if the data structure is as expected and contains 'playerstats' and 'achievements'
    if isinstance(data, dict) and 'playerstats' in data and \
       isinstance(data['playerstats'], dict) and 'achievements' in data['playerstats']:
        user_achievements = data['playerstats']['achievements']
    else:
        logger.error("Invalid data format. Expected 'playerstats' and 'achievements' keys.")
        return None

    unlock_times = []
    for ua in user_achievements:
        if isinstance(ua, dict) and 'unlocktime' in ua:
            try:
                unlock_time = DateUtils.convert_to_datetime(ua['unlocktime'])
                unlock_times.append(unlock_time)
            except ValueError as e:
                # Assuming ua['name'] exists for logging purposes
                logger.error(f"Error converting unlocktime for achievement {ua.get('name', 'Unknown')}: {e}")
        else:
            # Log an error or handle unexpected data format
            logger.error(f"Unexpected data format for achievement: {ua}")

    if not unlock_times:
        return None

    first_unlocktime = min(unlock_times)
    latest_unlocktime = max(unlock_times)
    time_span = DateUtils.calculate_time_span(first_unlocktime, latest_unlocktime)

    return DateUtils.format_time_span(time_span)

async def get_recent_achievements(game_achievements, user_achievements, user_game, user):
    if user_achievements is None:
        return []
    current_time = datetime.now().strftime(DATE_FORMAT)
    achievements = []

    # Sort the user_achievements list by unlocktime in descending order
    user_achievements.sort(key=lambda ua: ua.unlocktime, reverse=True)

    current_count = len([ua for ua in user_achievements if ua.achieved == 1])

    for user_achievement in user_achievements:
        if user_achievement.achieved == 1:
            matches = await find_matching_achievements(user_achievement, game_achievements, current_time, user_game, user)
            for match in matches:
                match += (current_count,)
                achievements.append(match)
                current_count -= 1  # Decrement the current count for each achievement

    return achievements

async def get_all_achievements(user_ids, api_keys):
    all_achievements = []
    for user_id, api_key in zip(user_ids, api_keys):
        achievements = await check_recently_played_games(user_id, api_key)
        all_achievements.extend(achievements)
    try:
        all_achievements.sort(key=lambda pair: datetime.strptime(pair[1].unlocktime, DATE_FORMAT))
    except Exception as e:
        logger.warning(f"Could not sort all_achievements: {e}")
        # leave unsorted if entries are malformed
    return all_achievements

def create_embed_info(game_achievement, user_achievement, user_game, current_count, total_achievements, user):
    # Steamhunters scraping removed; fall back to basic/default values
    ach_desc = getattr(game_achievement, 'description', '') or ''
    # Title will be the achievement name (made clickable by embed url)
    title = f"{user_achievement.name}"
    # Description contains only the achievement description (game link removed)
    description = ach_desc if ach_desc else ""

    logger.debug(f"Preparing to send embed for achievement: {user_achievement.name} in game: {user_game.name}")

    # Avoid division by zero
    try:
        completion_percentage = (current_count / total_achievements) * 100 if total_achievements else 0
    except Exception:
        completion_percentage = 0

    footer = f"{user.summary.personaname} • {user_achievement.unlocktime}"
    completion_info = f"{current_count}/{total_achievements} ({completion_percentage:.2f}%)"

    return title, description, completion_info, footer


async def check_recently_played_games(user_id, api_key):
    try:
        client = SteamClient(api_key)
        user = await get_user_games(user_id, api_key)
        recently_played_games = await get_recently_played_games(user)
        achievements = []
        for user_game in recently_played_games:
            result = await get_game_achievements(user_game, user, client)
            if result is None:
                continue
            game_achievement, user_achievement, total_achievements = result
            recent_achievements = await get_recent_achievements(game_achievement, user_achievement, user_game, user)
            for ach in recent_achievements:
                # `ach` is (game_achievement, user_achievement, user_game, user, current_count)
                # Return tuple as (game_achievement, user_achievement, user_game, user, total_achievements, current_count)
                ga, ua, ug, u, current_count = ach
                achievements.append((ga, ua, ug, u, total_achievements, current_count))
        return achievements
    except Exception as e:
        logger.error(f"Error processing achievements for user {user_id}: {e}")
        return []
    
async def create_and_send_embed(channel, game_achievement, user_achievement, user_game, user, total_achievements, current_count):
    color = await get_discord_color(user_game.game_icon)
    
    # Get information for the embed (title is achievement name)
    title, description, completion_info, footer = create_embed_info(game_achievement, user_achievement, user_game, current_count, total_achievements, user)

    # Create the embed with the game URL so the title is clickable
    embed = EmbedBuilder(title=title, description=description, color=discord.Color(color), url=user_game.url)
    embed.set_thumbnail(url=game_achievement.icon)
    # show the game as the author for clarity
    embed.set_author(name=user_game.name, icon_url=user_game.game_icon)
    
    # Add progress only — points/ratio no longer available via scraping
    embed.add_field(name="Progress", value=completion_info, inline=True)
    embed.set_footer(text=footer, icon_url=user.summary.avatarfull)
    
    logger.info(f"Sending embed for {user.summary.personaname}: {user_achievement.name} ({user_game.name})")
    
    # Send the embed to the channel
    await embed.send_embed(channel)

async def create_and_send_completion_embed(completion_channel, user_game, user, total_achievements, latest_unlocktime):
    color = await get_discord_color(user_game.game_icon)
    description = f"[{user.summary.personaname}]({user.summary.profileurl}) has completed all {total_achievements} achievements for [{user_game.name}]({user_game.url})!"
    embed = EmbedBuilder(description=description, color=discord.Color(color))
    # `get_user_achievements` returns the raw API response dict; guard if calculation fails
    try:
        completion_time_span = calculate_completion_time_span(user.get_user_achievements(user_game.appid))
    except Exception as e:
        logger.error(f"Error calculating completion time span: {e}")
        completion_time_span = None

    if completion_time_span is None:
        completion_time = "unknown"
    else:
        completion_time = str(completion_time_span).split('.')[0]  # Convert to string and remove microseconds
    # Rarest-achievement lookup removed (scraping no longer available)
    embed.set_author(name="Platinum unlocked", icon_url=PLATINUM_ICON)
    embed.set_thumbnail(url=user_game.game_icon)
    embed.set_footer(text=f"Platinum in {completion_time}", icon_url=user.summary.avatarfull)
    logger.info(f"Sending completion embed for {user.summary.personaname}: All achievements ({user_game.name})")
    await embed.send_embed(completion_channel)