import requests
from config.globals import STEAM_API_KEY

class SteamClient:
    def __init__(self):
        self.api_key = STEAM_API_KEY
        self.session = requests.Session()

    def _get(self, endpoint, params=None):
        if params is None:
            params = {}
        params['key'] = self.api_key
        response = self.session.get(f"https://api.steampowered.com/{endpoint}/", params=params)
        response.raise_for_status()
        return response.json()

    def user(self, steam_id):
        from .users import Users
        return Users(self, steam_id)

    def game(self):
        from .game import Game
        return Game(self)