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

# Define a dictionary to store the current count for each user
user_current_counts = {}

def normalize_whitespace(text):
    return re.sub(r'\s+', ' ', text).strip()

def get_achievement_page(app_id, page=1):
    url = f"https://completionist.me/steam/app/{app_id}/achievements?display=list&sort=created&order=desc&page={page}"
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
    page = 1
    achievement_dict = {}
    
    while True:
        soup = get_achievement_page(app_id, page)
        achievements = soup.find_all('strong')  # Adjust this selector if needed for accuracy
        
        if not achievements:  # If no achievements are found, exit the loop
            break

        for achievement in achievements:
            name, info = get_achievement_info(achievement)
            if name:
                achievement_dict[name] = info
        
        page += 1  # Move to the next page

    write_achievements_to_file(achievement_dict, app_id)
    return achievement_dict

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
    else:
        title = f"{user_achievement.name}"
        description = f"[{user_game.name}]({user_game.url})"

    completion_percentage = (current_count / total_achievements) * 100
    unlock_percentage = f"{achievement_info['percentage']}"
    footer = f"{user.summary.personaname} • {user_achievement.unlocktime}"
    completion_info = f"{current_count}/{total_achievements} ({completion_percentage:.2f}%)"
    return title, description, completion_info, unlock_percentage, footer

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
    title, description, completion_info, unlock_percentage, footer = create_embed_info(user_achievement, user_game, current_count, total_achievements, user)
    embed = EmbedBuilder(title=title, description=description, color=color)
    embed.set_thumbnail(url=game_achievement.icon)
    embed.set_author(name="Achievement unlocked", icon_url=user_game.game_icon)
    embed.add_field(name="Unlock Ratio", value=unlock_percentage, inline=True)
    embed.add_field(name="Progress", value=completion_info, inline=True)
    embed.set_footer(text=footer, icon_url=user.summary.avatarfull)
    logger.info(f"Sending embed for {user.summary.personaname}: {user_achievement.name} ({user_game.name})")
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