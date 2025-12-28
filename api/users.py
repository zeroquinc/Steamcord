from utils.datetime import DateUtils

class Users:
    """Class for fetching user-related data from Steam's API"""

    def __init__(self, client, steam_id: str):
        """Constructor for Users"""
        self.client = client
        self.steam_id = steam_id
        self.summary = None
        self.achievements = []
        self.owned_games = []

    def get_user_summaries(self):
        """Fetch user summaries"""
        endpoint = "ISteamUser/GetPlayerSummaries/v0002"
        params = {"steamids": self.steam_id}
        response = self.client._get(endpoint, params)
        self.summary = UserSummary(response['response']['players'][0])
        return response

    def get_owned_games(self):
        """Fetch owned games games"""
        endpoint = "IPlayerService/GetOwnedGames/v0001"
        params = {"steamid": self.steam_id, "include_appinfo": 1}  # Include game name and logo information
        response = self.client._get(endpoint, params)
        self.owned_games = [UserOwnedGame(game) for game in response['response']['games']]
        return response
    
    def get_recently_played_games(self, count: int = 50):
        """Fetch recently played games (covers family-shared games).

        Populates `self.recently_played_games` with `UserRecentlyPlayedGame` objects.
        """
        endpoint = "IPlayerService/GetRecentlyPlayedGames/v1"
        params = {"steamid": self.steam_id, "count": count}
        response = self.client._get(endpoint, params)
        games = response.get('response', {}).get('games', [])
        self.recently_played_games = [UserRecentlyPlayedGame(g) for g in games]
        return response
    
    def get_user_achievements(self, app_id: str, l: str = "en"):
        """Fetch user achievements"""
        endpoint = "ISteamUserStats/GetPlayerAchievements/v0001"
        params = {"steamid": self.steam_id, "appid": app_id, "l": l}
        response = self.client._get(endpoint, params)
        if 'achievements' in response['playerstats']:
            self.achievements = [UserAchievement(a, app_id) for a in response['playerstats']['achievements']]
        else:
            self.achievements = []
        return response

class UserAchievement:
    def __init__(self, data, appid):  # Add appid parameter
        self.appid = appid  # Store appid
        self.apiname = data['apiname']
        self.achieved = data['achieved']
        self.unlocktime = DateUtils.format_timestamp(data['unlocktime'])
        self.name = data['name']
        self.description = data.get('description', '')

class UserSummary:
    def __init__(self, data):
        self.personaname = data['personaname']
        self.profileurl = data['profileurl']
        self.avatarfull = data['avatarfull']
        self.lastonline = DateUtils.format_timestamp(data['lastlogoff'])
        self.timecreated = DateUtils.format_timestamp(data['timecreated'])
        self.age = DateUtils.calculate_age(data['timecreated'])

class UserOwnedGame:
    def __init__(self, game_dict):
        self.appid = game_dict['appid']
        self.name = game_dict.get('name', '')
        self.url = f"https://store.steampowered.com/app/{game_dict['appid']}"
        try:
            self.game_icon = f"http://media.steampowered.com/steamcommunity/public/images/apps/{game_dict['appid']}/{game_dict['img_icon_url']}.jpg"
            self.last_played = DateUtils.format_timestamp(game_dict['rtime_last_played'])
        except KeyError:
            self.game_icon = ""
            self.last_played = "Unknown"


class UserRecentlyPlayedGame:
    def __init__(self, game_dict):
        self.appid = game_dict.get('appid')
        self.name = game_dict.get('name', '')
        self.url = f"https://store.steampowered.com/app/{self.appid}"
        # Build icon URL when available
        img_icon = game_dict.get('img_icon_url') or game_dict.get('img_logo_url') or ''
        if img_icon:
            self.game_icon = f"http://media.steampowered.com/steamcommunity/public/images/apps/{self.appid}/{img_icon}.jpg"
        else:
            self.game_icon = ""
        # recently-played may provide a last_played or rtime_last_played field; fall back safely
        last_played_ts = game_dict.get('rtime_last_played') or game_dict.get('last_played')
        try:
            self.last_played = DateUtils.format_timestamp(last_played_ts) if last_played_ts is not None else "Unknown"
        except Exception:
            self.last_played = "Unknown"