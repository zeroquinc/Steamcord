from datetime import datetime, timedelta
from dateutil.parser import parse

from api.client import SteamClient
from config.globals import STEAM_API_KEY1, STEAM_API_KEY2

def check_achievement_completion(user_id, game_id, api_key):
    # Create a SteamClient instance with the provided API key
    client = SteamClient(api_key)

    # Create a Game instance and fetch game achievements
    game = client.game()
    game.get_game_achievements(game_id)

    # Create a Users instance and fetch user achievements and user summary
    user = client.user(user_id)
    user.get_user_achievements(game_id)
    user.get_user_summaries()

    # Count the number of achievements the user has completed
    completed_achievements = sum(1 for a in user.achievements if a.achieved == 1)

    print("User Information")
    print(f"Username: {user.summary.personaname}")
    print(f"Profile URL: {user.summary.profileurl}")
    print(f"Creation Date: {user.summary.timecreated}")
    print(f"Account Age: {user.summary.age}")
    print(f"Last Online: {user.summary.lastonline}")
    print()
    print("Game Information")
    print(f"Game Name: {game.gamename}")
    print(f"Total Achievements: {len(game.achievements)}")
    # Print each achievement name
    print("Achievements:")
    achievement_count = 0
    for achievement in user.achievements:
        if achievement.achieved == 1:
            achievement_count += 1
            print(f"{achievement_count}. {achievement.name}")
    print(f"Completed Achievements: {completed_achievements}")
    print()

def check_recently_played_games(user_id, api_key):
    # Create a SteamClient instance with the provided API key
    client = SteamClient(api_key)

    # Create a User instance and fetch user's owned games
    user = client.user(user_id)
    user.get_user_summaries()

    owned_games = user.get_owned_games()

    # Get the current timestamp
    current_timestamp = datetime.now().timestamp()

    print(f"Recently Played Games for User: {user.summary.personaname}")
    for game in owned_games['response']['games']:
        # Check if the game has been played within the last 24 hours
        if game['rtime_last_played'] != 0 and current_timestamp - game['rtime_last_played'] <= 24 * 60 * 60:
            # Create a Game instance and fetch game achievements
            game_instance = client.game()
            game_instance.get_game_achievements(game['appid'])

            # Count the total number of achievements for the game
            total_achievements = len(game_instance.achievements)

            # Fetch the user's achievements for the game
            user.get_user_achievements(game['appid'])

            # Count the number of achievements the user has completed
            completed_achievements = sum(1 for a in user.achievements if a.achieved == 1)

            print(f"Game Name: {game['name']}")
            print(f"Total Achievements: {total_achievements}")
            print(f"Completed Achievements: {completed_achievements}")
            print()

# Usage:
#check_achievement_completion('76561198035515815', '504230', STEAM_API_KEY1)
#check_achievement_completion('76561198840513734', '504230', STEAM_API_KEY2)
check_recently_played_games('76561198035515815', STEAM_API_KEY1)
check_recently_played_games('76561198840513734', STEAM_API_KEY2)