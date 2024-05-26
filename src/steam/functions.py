from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re
import json
import os

from api.client import SteamClient
from utils.custom_logger import logger

DATE_FORMAT = '%d/%m/%y %H:%M:%S'

async def check_recently_played_games(user_id, api_key):
    try:
        # Create a SteamClient instance with the provided API key
        client = SteamClient(api_key)
        # Create a User instance and fetch user's owned games
        user = client.user(user_id)
        user.get_user_summaries()
        user.get_owned_games()
        # Get the current timestamp and format it to match unlocktime
        current_time = datetime.now().strftime(DATE_FORMAT)
        achievements = []
        for user_game in user.owned_games:
            # Check if the game has been played within the last 24 hours
            if user_game.last_played != "Unknown":
                last_played_date = datetime.strptime(user_game.last_played, DATE_FORMAT)
                if datetime.strptime(current_time, DATE_FORMAT) - last_played_date <= timedelta(days=20):
                    game_instance = client.game()
                    game_instance.get_game_achievements(user_game.appid)
                    # Fetch the user's achievements for the game
                    user.get_user_achievements(user_game.appid)
                    # Iterate over the user's achievements
                    for user_achievement in user.achievements:
                        # Check if the achievement was unlocked
                        if user_achievement.achieved == 1:
                            # Iterate over the game's achievements
                            for game_achievement in game_instance.achievements:
                                # Check if the names match
                                if game_achievement.displayname == user_achievement.name:
                                    # Check if the achievement was unlocked within the last 24 hours
                                    unlocktime = datetime.strptime(user_achievement.unlocktime, DATE_FORMAT)
                                    if unlocktime and datetime.strptime(current_time, DATE_FORMAT) - unlocktime <= timedelta(days=20):
                                        # Add the game achievement and the corresponding user_achievement to the achievements list
                                        achievements.append((game_achievement, user_achievement, user_game, user))
        return achievements
    except Exception as e:
        logger.error(f"Error processing achievements for user {user_id}: {e}")
        return []

def normalize_whitespace(text):
    return re.sub(r'\s+', ' ', text).strip()

def scrape_all_achievements(app_id):
    url = f"https://completionist.me/steam/app/{app_id}/achievements"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Find all achievements
    achievements = soup.find_all('strong')
    # Create a dictionary of achievement names and descriptions
    achievement_dict = {}
    for achievement in achievements:
        name = normalize_whitespace(achievement.text)
        description_span = achievement.find_next_sibling('span', class_='text-muted')
        if description_span:
            description = normalize_whitespace(description_span.text)
            percentage_tds = achievement.parent.find_next_siblings('td', class_='text-center')
            if len(percentage_tds) > 1 and percentage_tds[1].find('small'):
                percentage = normalize_whitespace(percentage_tds[1].find('small').text)
            else:
                percentage = 'Unknown'
            achievement_dict[name] = {'description': description, 'percentage': percentage}
    # Define the file path
    file_path = os.path.join(os.path.dirname(__file__), 'data', f'achievements_{app_id}.json')
    # Write the dictionary to a file
    with open(file_path, 'w') as f:
        json.dump(achievement_dict, f)
    return achievement_dict

def get_achievement_description(app_id, achievement_name):
    # Define the file path
    file_path = os.path.join(os.path.dirname(__file__), 'data', f'achievements_{app_id}.json')
    # Try to load the achievements from a file
    try:
        with open(file_path, 'r') as f:
            achievement_dict = json.load(f)
        logger.info(f'Loaded achievements for app {app_id} from JSON file')
    except FileNotFoundError:
        # If the file doesn't exist, scrape the achievements
        logger.info(f'File not found, scraping achievements for app {app_id}')
        achievement_dict = scrape_all_achievements(app_id)
    # Return the description of the given achievement
    return achievement_dict.get(achievement_name)