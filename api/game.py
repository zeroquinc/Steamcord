class Game:
    def __init__(self, client):
        self.client = client
        self.gamename = None
        self.gameversion = None
        self.achievements = []

    def get_game_achievements(self, app_id, l="en"):
        """Fetch game achievements"""
        endpoint = 'ISteamUserStats/GetSchemaForGame/v2/'
        params = {'key': self.client.api_key, 'appid': app_id, 'l': l}
        response = self.client._get(endpoint, params)
        print(response)
        self.gamename = response['game']['gameName']
        self.gameversion = response['game']['gameVersion']
        if 'achievements' in response['game']['availableGameStats']:
            self.achievements = [GameAchievement(a) for a in response['game']['availableGameStats']['achievements']]
        else:
            self.achievements = []
        return response

class GameAchievement:
    def __init__(self, data):
        self.name = data['name']
        self.defaultvalue = data['defaultvalue']
        self.displayname = data['displayName']
        self.hidden = data['hidden']
        self.description = data.get('description', '')
        self.icon = data['icon']
        self.icongray = data['icongray']