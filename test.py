from api.client import SteamClient

def check_achievement_completion(user_ids, game_id):
    # Create a SteamClient instance
    client = SteamClient()

    # Create a Game instance and fetch game achievements
    game = client.game()
    game.get_game_achievements(game_id)

    for user_id in user_ids:
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
        print(f"Completed Achievements: {completed_achievements}")
        print()

# Usage:
check_achievement_completion(['76561198035515815', '76561198840513734'], '504230')