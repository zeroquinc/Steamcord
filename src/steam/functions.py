from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re
import json
import os

from api.client import SteamClient
from config.globals import ACHIEVEMENT_TIME
from utils.custom_logger import logger

DATE_FORMAT = '%d/%m/%y %H:%M:%S'

# Define a dictionary to store the current count for each user
user_current_counts = {}

def normalize_whitespace(text):
    return re.sub(r'\s+', ' ', text).strip()

def get_achievement_page(app_id):
    url = f"https://completionist.me/steam/app/{app_id}/achievements"
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')

def get_achievement_info(achievement):
    name = normalize_whitespace(achievement.text)
    description_span = achievement.find_next_sibling('span', class_='text-muted')
    description = normalize_whitespace(description_span.text) if description_span else None
    percentage_tds = achievement.parent.find_next_siblings('td', class_='text-center')
    percentage = normalize_whitespace(percentage_tds[1].find('small').text) if len(percentage_tds) > 1 and percentage_tds[1].find('small') else 'Unknown'
    return name, {'description': description, 'percentage': percentage}

def write_achievements_to_file(achievement_dict, app_id):
    dir_path = os.path.join(os.path.dirname(__file__), 'data')
    file_path = os.path.join(dir_path, f'achievements_{app_id}.json')
    logger.debug(f'Writing achievements to file: {file_path}')
    try:
        os.makedirs(dir_path, exist_ok=True)  # This will create the directory if it doesn't exist
        with open(file_path, 'w') as f:
            json.dump(achievement_dict, f)
        logger.debug(f'Successfully wrote achievements to file: {file_path}')
    except Exception as e:
        logger.error(f'Error writing achievements to file: {file_path}, Error: {e}')

def scrape_all_achievements(app_id):
    soup = get_achievement_page(app_id)
    achievements = soup.find_all('strong')
    achievement_dict = {}
    for achievement in achievements:
        name, info = get_achievement_info(achievement)
        if name:
            achievement_dict[name] = info
    write_achievements_to_file(achievement_dict, app_id)
    return achievement_dict

def load_achievements_from_file(app_id):
    file_path = os.path.join(os.path.dirname(__file__), 'data', f'achievements_{app_id}.json')
    try:
        with open(file_path, 'r') as f:
            achievement_dict = json.load(f)
        logger.info(f'Loaded achievements for app {app_id} from JSON file')
    except FileNotFoundError:
        logger.info(f'File not found, scraping achievements for app {app_id}')
        achievement_dict = scrape_all_achievements(app_id)
    return achievement_dict

def get_achievement_description(app_id, achievement_name):
    achievement_dict = load_achievements_from_file(app_id)
    return achievement_dict.get(achievement_name)

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
    game_instance.get_game_achievements(user_game.appid)
    user.get_user_achievements(user_game.appid)
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

async def get_recent_achievements(game_achievements, user_achievements, user_game, user):
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

def create_embed_description_footer(user_achievement, user_game, total_achievements, current_count):
    if achievement_info := get_achievement_description(user_game.appid, user_achievement.name):
        description = f"**{user_achievement.name}** <:silver:1242467048035192955> **{achievement_info['percentage']}**\n{achievement_info['description']}\n\n[{user_game.name}]({user_game.url})"
    else:
        description = f"**{user_achievement.name}**"

    completion_percentage = (current_count / total_achievements) * 100
    footer = f"{user_achievement.unlocktime} • {current_count}/{total_achievements} ({completion_percentage:.2f}%)"
    return description, footer

async def check_recently_played_games(user_id, api_key):
    try:
        client = SteamClient(api_key)
        user = await get_user_games(user_id, api_key)
        recently_played_games = await get_recently_played_games(user)
        achievements = []
        for user_game in recently_played_games:
            result = await get_game_achievements(user_game, user, client)
            logger.debug(f"get_game_achievements returned: {result}")
            game_achievement, user_achievement, total_achievements = result
            recent_achievements = await get_recent_achievements(game_achievement, user_achievement, user_game, user)
            for ach in recent_achievements:
                achievements.append(ach + (total_achievements,))  # Create a new tuple that includes total achievements
        return achievements
    except Exception as e:
        logger.error(f"Error processing achievements for user {user_id}: {e}")
        return []