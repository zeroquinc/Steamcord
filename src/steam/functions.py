from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re
import json
import os

from api.client import SteamClient
from config.globals import ACHIEVEMENT_TIME, PLATINUM_ICON
from src.discord.embed import EmbedBuilder
from utils.image import get_discord_color
from utils.datetime import DateUtils
from utils.custom_logger import logger

DATE_FORMAT = '%d/%m/%y %H:%M:%S'

# Mapping of tag IDs to descriptions
TAG_MAPPING = {
    3: "Main Storyline",
    9: "Collectible",
    13: "Choice Dependent",
    11: "Speedrun",
    1: "Missable"
}

# Define a dictionary to store the current count for each user
user_current_counts = {}

def normalize_whitespace(text):
    return re.sub(r'\s+', ' ', text).strip()

def get_achievement_page(app_id):
    url = f"https://steamhunters.com/apps/{app_id}/achievements"
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')

def get_achievement_info(achievement):
    # Extract information from the parsed JSON-like structure in the page
    try:
        api_name = achievement.get('apiName', 'Unknown')
        name = achievement.get('name', 'Unknown')
        description = achievement.get('description', 'No description provided')
        percentage = achievement.get('steamPercentage', 'Unknown')
        points = achievement.get('points', 'Unknown')
        
        return name, {
            'api_name': api_name,
            'description': description,
            'percentage': percentage,
            'points': points
        }
    except KeyError as e:
        print(f"Error extracting achievement info: {e}")
        return None, None

def write_achievements_to_file(achievement_dict, app_id):
    dir_path = os.path.join(os.path.dirname(__file__), 'data')
    file_path = os.path.join(dir_path, f'achievements_{app_id}.json')
    print(f'Writing achievements to file: {file_path}')
    try:
        os.makedirs(dir_path, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(achievement_dict, f, indent=4)
        print(f'Successfully wrote achievements to file: {file_path}')
    except Exception as e:
        print(f'Error writing achievements to file: {file_path}, Error: {e}')

import re

# Mapping of tag IDs to descriptions
TAG_MAPPING = {
    3: "Main Storyline",
    9: "Collectible",
    13: "Choice Dependent",
    11: "Speedrun",
    1: "Missable"
}

def scrape_all_achievements(app_id):
    logger.debug(f"Scraping achievements for app ID: {app_id}")
    soup = get_achievement_page(app_id)

    script_tag = soup.find('script', text=lambda t: 'var sh =' in t if t else False)
    if not script_tag:
        logger.error("Error: Could not find the achievement data on the page.")
        return {}

    try:
        script_content = script_tag.string
        start_index = script_content.find('model:') + len('model:')
        end_index = script_content.find('requestHttpMethod:')

        if end_index == -1:
            raw_json = script_content[start_index:].strip().rstrip(',').strip()
        else:
            raw_json = script_content[start_index:end_index].strip().rstrip(',').strip()

        logger.debug(f"Extracted raw JSON length: {len(raw_json)}")

        # Replace `new Date(...)` with a placeholder or remove it
        raw_json = re.sub(r'new Date\([0-9]+\)', '"PLACEHOLDER_DATE"', raw_json)

        if not raw_json or not raw_json.startswith('{') or not raw_json.endswith('}'):
            logger.error("Extracted JSON appears incomplete or invalid.")
            return {}

        data = json.loads(raw_json)
        achievements = data['listData']['pagedList']['items']
        achievement_dict = {}

        for achievement in achievements:
            name, info = get_achievement_info(achievement)
            if name:
                # Use only steamPercentage and round it to 1 decimal place
                steam_percentage = round(achievement.get("steamPercentage", 0), 1)
                
                # Round points to a whole number
                points = round(achievement.get("points", 0))

                # Extract and map tags
                tags = achievement.get("tagVotes", [])
                mapped_tags = [TAG_MAPPING[tag["tagId"]] for tag in tags if tag["tagId"] in TAG_MAPPING]

                # Build the final info dictionary
                info.update({
                    "steamPercentage": steam_percentage,
                    "points": points,
                    "tags": mapped_tags
                })

                achievement_dict[name] = info

        logger.debug(f"Parsed achievement data for app ID {app_id}: {achievement_dict}")
        write_achievements_to_file(achievement_dict, app_id)
        return achievement_dict

    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error for app ID {app_id}: {e.doc[e.pos-50:e.pos+50]}")
    except Exception as e:
        logger.error(f"Error parsing achievements data for app ID {app_id}: {e}")

    return {}

def load_achievements_from_file(app_id):
    file_path = os.path.join(os.path.dirname(__file__), 'data', f'achievements_{app_id}.json')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            achievement_dict = json.load(f)
        logger.debug(f'Loaded achievements for app {app_id} from JSON file')
    except FileNotFoundError:
        logger.debug(f'File not found, scraping achievements for app {app_id}')
        achievement_dict = scrape_all_achievements(app_id)
    return achievement_dict

def find_rarest_achievement(app_id):
    achievement_dict = load_achievements_from_file(app_id)
    if not achievement_dict:
        return None
    
    lowest_percentage = None
    rarest_achievement_name = None
    for name, info in achievement_dict.items():
        percentage_str = info.get('percentage', 'Unknown')
        if percentage_str != 'Unknown':
            percentage = float(percentage_str.replace('%', ''))
            if lowest_percentage is None or percentage < lowest_percentage:
                lowest_percentage = percentage
                rarest_achievement_name = name
    
    if rarest_achievement_name:
        return f"{rarest_achievement_name} ({lowest_percentage}%)"
    else:
        return None

def get_achievement_description(app_id, achievement_name):
    achievement_dict = load_achievements_from_file(app_id)
    logger.debug(f"Looking for achievement: {achievement_name}")
    # Normalize the achievement_name before searching
    achievement_name = achievement_name.strip().lower()
    # Normalize the keys in achievement_dict
    achievement_dict = {k.strip().lower(): v for k, v in achievement_dict.items()}
    achievement = achievement_dict.get(achievement_name)
    if achievement is None:
        logger.debug(f"Achievement not found: {achievement_name}")
    else:
        logger.debug(f"Loaded achievement: {achievement}")
    return achievement

async def get_user_games(user_id, api_key):
    client = SteamClient(api_key)
    user = client.user(user_id)
    user.get_user_summaries()
    user.get_owned_games()
    return user

async def get_recently_played_games(user):
    current_time = datetime.now().strftime(DATE_FORMAT)
    recently_played_games = []
    for user_game in user.owned_games:
        if user_game.last_played != "Unknown":
            last_played_date = datetime.strptime(user_game.last_played, DATE_FORMAT)
            if datetime.strptime(current_time, DATE_FORMAT) - last_played_date <= timedelta(minutes=ACHIEVEMENT_TIME):
                recently_played_games.append(user_game)
    return recently_played_games

async def get_game_achievements(user_game, user, client):
    game_instance = client.game()
    try:
        game_instance.get_game_achievements(user_game.appid)
    except KeyError as e:
        logger.error(f"Error processing achievements for game {user_game.appid}: {e}")
        return None, None, 0
    user.get_user_achievements(user_game.appid)
    if not game_instance.achievements:
        return None, None, 0
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
    all_achievements.sort(key=lambda pair: datetime.strptime(pair[1].unlocktime, DATE_FORMAT))
    return all_achievements

def create_embed_info(user_achievement, user_game, total_achievements, current_count, user):
    if achievement_info := get_achievement_description(user_game.appid, user_achievement.name):
        title = f"{user_achievement.name}"
        description = f"{achievement_info['description']}\n\n[{user_game.name}]({user_game.url})"
        points = achievement_info.get("points", 0)  # Extract points
        tags = achievement_info.get("tags", [])     # Extract tags
    else:
        title = f"{user_achievement.name}"
        description = f"[{user_game.name}]({user_game.url})"
        points = 0  # Default points if not available
        tags = []

    logger.debug(f"Preparing to send embed for achievement: {user_achievement.name} in game: {user_game.name}")

    completion_percentage = (current_count / total_achievements) * 100
    unlock_percentage = f"{achievement_info['steamPercentage']}"
    footer = f"{user.summary.personaname} • {user_achievement.unlocktime}"
    completion_info = f"{current_count}/{total_achievements} ({completion_percentage:.2f}%)"
    
    return title, description, completion_info, unlock_percentage, footer, points, tags


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
                achievements.append(ach + (total_achievements,))  # Create a new tuple that includes total achievements
        return achievements
    except Exception as e:
        logger.error(f"Error processing achievements for user {user_id}: {e}")
        return []
    
async def create_and_send_embed(channel, game_achievement, user_achievement, user_game, user, total_achievements, current_count):
    color = await get_discord_color(user_game.game_icon)
    
    # Get information for the embed
    title, description, completion_info, unlock_percentage, footer, points, tags = create_embed_info(user_achievement, user_game, current_count, total_achievements, user)
    
    # Create the embed
    embed = EmbedBuilder(title=title, description=description, color=color)
    embed.set_thumbnail(url=game_achievement.icon)
    embed.set_author(name="Achievement unlocked", icon_url=user_game.game_icon)
    
    # Add Tags field only if there are tags
    if tags:  # Only add if tags are not empty
        embed.add_field(name="Category", value=", ".join(tags), inline=False)
    
    # Add the existing fields
    embed.add_field(name="Unlock Ratio", value=f"{unlock_percentage}%", inline=True)
    embed.add_field(name="Points", value=str(points), inline=True)
    embed.add_field(name="Progress", value=completion_info, inline=True)
    embed.set_footer(text=footer, icon_url=user.summary.avatarfull)
    
    logger.info(f"Sending embed for {user.summary.personaname}: {user_achievement.name} ({user_game.name})")
    
    # Send the embed to the channel
    await embed.send_embed(channel)

async def create_and_send_completion_embed(completion_channel, user_game, user, total_achievements, latest_unlocktime):
    color = await get_discord_color(user_game.game_icon)
    description = f"[{user.summary.personaname}]({user.summary.profileurl}) has completed all {total_achievements} achievements for [{user_game.name}]({user_game.url})!"
    embed = EmbedBuilder(description=description, color=color)
    completion_time_span = calculate_completion_time_span(user.get_user_achievements(user_game.appid))
    completion_time = str(completion_time_span).split('.')[0]  # Convert to string and remove microseconds
    # Get the description of the rarest achievement
    rarest_achievement = find_rarest_achievement(user_game.appid)
    if rarest_achievement:
        embed.add_field(name="Rarest Achievement", value=rarest_achievement, inline=False)
    embed.set_author(name="Platinum unlocked", icon_url=PLATINUM_ICON)
    embed.set_thumbnail(url=user_game.game_icon)
    embed.set_footer(text=f"Platinum in {completion_time}", icon_url=user.summary.avatarfull)
    logger.info(f"Sending completion embed for {user.summary.personaname}: All achievements ({user_game.name})")
    await embed.send_embed(completion_channel)