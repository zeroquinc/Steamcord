# Steamcord
A Discord bot for Steam embeds

## Examples

<table>
  <tr>
    <td>
      <img src="" alt="image1">
    </td>
    <td>
      <img src="" alt="image2">
    </td>
  </tr>
</table>

## Getting your Steam API Key

To get your Steam API Key, follow these steps:

1. Go to the Steam API Key page at `https://steamcommunity.com/dev/apikey`.
2. If you're not already logged in, you'll be asked to log in with your Steam account.
3. Once logged in, you'll be asked to enter a domain name. This can be any valid domain name that you own, or a placeholder if you're just using the key for personal use.
4. After entering a domain name, click on "Register".
5. You'll be presented with your new API Key. Make sure to keep this key safe, as it gives access to Steam's APIs with your account.

## Getting a Discord Bot

To create a Discord bot, follow these steps:

1. Go to the Discord Developer Portal at `https://discord.com/developers/applications`.
2. Click on the "New Application" button.
3. Give your application a name and click "Create".
4. On the left-hand side, click on "Bot".
5. Click on the "Add Bot" button on the right.
6. You'll now have created a new bot. Under the bot's username, you'll see a section called "Token". Click on "Copy" to copy your bot's token. This is what you'll use to log in to the bot and control it.
7. To add the bot to a server, go to the "OAuth2" section on the left-hand side.
8. Under "Scopes", select "bot".
9. Under "Bot Permissions", select the permissions your bot needs.
10. Copy the generated URL and open it in your web browser to add the bot to a server you have manage permissions on.

Remember to keep your bot's token safe, as anyone with the token can control your bot.

## How to use

1. Fill in your Steam API key and Steam ID, your Steam ID can be found [here](https://www.steamidfinder.com/)
2. Rename env to .env and fill in the variables
3. Pip install `requirements.txt`
4. Run `main.py`