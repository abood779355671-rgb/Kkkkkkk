# Telegram Bot & Userbot

A powerful Telegram bot and userbot built with Python, featuring group management, RSS feeds, PM permit, and more.

## Features

- **Bot & Userbot Support** - Run as a bot, userbot, or both simultaneously
- **Group Management** - Welcome messages, global bans, and moderation tools
- **PM Permit** - Control who can message you privately
- **RSS Feeds** - Subscribe to and receive RSS feed updates
- **Logging** - Log mentions, messages, and moderation actions
- **ARQ API Integration** - Access various ARQ services

## Requirements

- Python 3.8+
- MongoDB database
- Telegram API credentials

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/your-repo.git
cd your-repo
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the sample configuration file and fill in your values:

```bash
cp sample_config.env config.env
```

Edit `config.env` with your credentials (see Configuration section below).

### 4. Run the bot

```bash
python main.py
```

## Configuration

Create a `config.env` file with the following variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | Yes | Telegram bot token from [@BotFather](https://t.me/BotFather) |
| `API_ID` | Yes | Telegram API ID from [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | Yes | Telegram API Hash from [my.telegram.org](https://my.telegram.org) |
| `MONGO_URL` | Yes | MongoDB connection URI |
| `LOG_GROUP_ID` | Yes | Chat ID for logging bot activities |
| `GBAN_LOG_GROUP_ID` | Yes | Chat ID for global ban logs |
| `MESSAGE_DUMP_CHAT` | Yes | Chat ID for message dumps |
| `SESSION_STRING` | No | Pyrogram session string for userbot functionality |
| `PHONE_NUMBER` | No | Phone number for userbot (alternative to session string) |
| `USERBOT_PREFIX` | No | Command prefix for userbot (default: `\`) |
| `SUDO_USERS_ID` | No | Space-separated list of user IDs with sudo access |
| `WELCOME_DELAY_KICK_SEC` | No | Seconds to wait before kicking unverified users (default: `600`) |
| `ARQ_API_KEY` | No | API key for ARQ services |
| `ARQ_API_URL` | No | ARQ API URL (default: `https://arq.hamker.dev`) |
| `LOG_MENTIONS` | No | Log mentions in groups (default: `True`) |
| `RSS_DELAY` | No | Delay between RSS feed checks in seconds (default: `300`) |
| `PM_PERMIT` | No | Enable PM permit feature (default: `True`) |

### Example config.env

```env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
MONGO_URL=mongodb+srv://user:password@cluster.mongodb.net/database
LOG_GROUP_ID=-1001234567890
GBAN_LOG_GROUP_ID=-1001234567891
MESSAGE_DUMP_CHAT=-1001234567892
SUDO_USERS_ID=123456789 987654321
WELCOME_DELAY_KICK_SEC=600
LOG_MENTIONS=True
PM_PERMIT=True
RSS_DELAY=300
```

## Getting API Credentials

### Telegram API ID & Hash
1. Go to [my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Click on "API development tools"
4. Create a new application
5. Copy the `api_id` and `api_hash`

### Bot Token
1. Open [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the instructions
3. Copy the bot token provided

### Session String (for Userbot)
Generate a Pyrogram session string using the Pyrogram library or online generators.

### MongoDB
1. Create a free cluster at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Get your connection string from the cluster dashboard

## License

This project is open source. Feel free to use and modify as needed.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.