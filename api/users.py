from datetime import datetime

from utils.datetime import DateUtils

class Users:
    """Class for fetching user-related data from Steam's API"""

    def __init__(self, client, steam_id: str):
        """Constructor for Users"""
        self.client = client
        self.steam_id = steam_id
        self.summary = None
        self.achievements = []

    def get_user_summaries(self):
        """Fetch user summaries"""
        endpoint = "ISteamUser/GetPlayerSummaries/v0002"
        params = {"steamids": self.steam_id}
        response = self.client._get(endpoint, params)
        self.summary = UserSummary(response['response']['players'][0])
        return response

    def get_recently_played_games(self):
        """Fetch recently played games"""
        endpoint = "IPlayerService/GetRecentlyPlayedGames/v0001"
        params = {"steamid": self.steam_id}
        return self.client._get(endpoint, params)
    
    def get_user_achievements(self, app_id: str, l: str = "en"):
        """Fetch user achievements"""
        endpoint = "ISteamUserStats/GetPlayerAchievements/v0001"
        params = {"steamid": self.steam_id, "appid": app_id, "l": l}
        response = self.client._get(endpoint, params)
        self.achievements = [UserAchievement(a) for a in response['playerstats']['achievements']]
        return response
    
class UserAchievement:
    def __init__(self, data):
        self.apiname = data['apiname']
        self.achieved = data['achieved']
        self.unlocktime = data['unlocktime']
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