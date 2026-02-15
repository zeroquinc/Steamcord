class Game:
    def __init__(self, client):
        self.client = client
        self.gamename = None
        self.gameversion = None
        self.achievements = []

    def get_game_achievements(self, app_id, l="en"):
        """Fetch game achievements. Be defensive against missing/changed API fields."""
        endpoint = 'ISteamUserStats/GetSchemaForGame/v2/'
        params = {'key': self.client.api_key, 'appid': app_id, 'l': l}
        response = self.client._get(endpoint, params)

        if not isinstance(response, dict):
            # Unexpected response type; fail closed and avoid exceptions
            self.gamename = None
            self.gameversion = None
            self.achievements = []
            return response

        game = response.get('game')
        if not isinstance(game, dict):
            # No game schema returned (e.g., private/unavailable game)
            self.gamename = None
            self.gameversion = None
            self.achievements = []
            return response

        # Use .get to avoid KeyError if API response changes
        self.gamename = game.get('gameName') or game.get('name')
        self.gameversion = game.get('gameVersion')

        available_stats = game.get('availableGameStats', {})
        if not isinstance(available_stats, dict):
            self.achievements = []
            return response
        achievements = available_stats.get('achievements')
        if isinstance(achievements, list):
            self.achievements = [GameAchievement(a) for a in achievements if isinstance(a, dict) and 'name' in a]
        else:
            self.achievements = []

        return response

class GameAchievement:
    def __init__(self, data):
        # Be defensive and provide sensible defaults if keys are missing
        self.name = data.get('name')
        self.defaultvalue = data.get('defaultvalue')
        self.displayname = data.get('displayName') or data.get('name')
        self.hidden = data.get('hidden', 0)
        self.description = data.get('description', '')
        self.icon = data.get('icon', '')
        self.icongray = data.get('icongray', '')