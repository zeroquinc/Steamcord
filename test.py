from datetime import datetime, timedelta

from api.client import SteamClient
from utils.embed import EmbedBuilder
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
    user.get_owned_games()

    # Get the current timestamp and format it to match unlocktime
    current_time = datetime.now().strftime('%d/%m/%y %H:%M:%S')

    print(f"Recently Played Games for User: {user.summary.personaname}")
    for user_game in user.owned_games:
        # Check if the game has been played within the last 24 hours
        if user_game.last_played != "Unknown":
            last_played_date = datetime.strptime(user_game.last_played, '%d/%m/%y %H:%M:%S')
            if datetime.strptime(current_time, '%d/%m/%y %H:%M:%S') - last_played_date <= timedelta(days=20):
                # Create a Game instance and fetch game achievements
                game_instance = client.game()
                game_instance.get_game_achievements(user_game.appid)

                # Fetch the user's achievements for the game
                user.get_user_achievements(user_game.appid, game_instance=game_instance)

                print(f"Game Name: {user_game.name}")
                print("Achievements unlocked in the last 10 days:")
                print()

                # Store achievements in a list
                achievements = []

                # Iterate over the user's achievements
                for a in user.achievements:
                    # Check if the achievement was unlocked and if it was unlocked within the last 24 hours
                    if a.achieved == 1:
                        unlocktime = datetime.strptime(a.unlocktime, '%d/%m/%y %H:%M:%S')
                        if unlocktime and datetime.strptime(current_time, '%d/%m/%y %H:%M:%S') - unlocktime <= timedelta(days=20):
                            achievements.append(a)

                # Sort achievements by unlocktime
                achievements.sort(key=lambda a: datetime.strptime(a.unlocktime, '%d/%m/%y %H:%M:%S'))

                # Print achievements
                for a in achievements:
                    print(f"Name of Achievement: {a.name}")
                    print(f"Date of Unlocktime: {a.unlocktime}")
                    print(f"Details: {a.description}")
                    print(f"Icon URL: {a.icon}")
                    print()

# Usage:
#check_achievement_completion('76561198035515815', '504230', STEAM_API_KEY1)
#check_achievement_completion('76561198840513734', '504230', STEAM_API_KEY2)
check_recently_played_games('76561198035515815', STEAM_API_KEY1)
check_recently_played_games('76561198840513734', STEAM_API_KEY2)