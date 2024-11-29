# Social Media Cross-Posting Bot

A powerful Telegram bot that automatically cross-posts content to multiple social media platforms (Twitter/X, Bluesky, and Farcaster) based on community reactions.

## Features

- **Automated Cross-Posting**: Automatically shares content across multiple platforms when reaction threshold is met
- **Media Support**: Handles text, images, videos, and GIFs
- **Reaction-Based**: Posts are shared only after receiving sufficient community approval (default: 7 reactions)
- **Time-Sensitive**: Posts expire after 2 hours to maintain content relevance
- **Clean Interface**: Minimal bot interaction in group chats
- **Docker Support**: Easy deployment using Docker containers

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for containerized deployment)
- API credentials for:
  - Telegram Bot
  - Twitter/X Developer Account
  - Bluesky Social
  - Farcaster

## Installation

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/developerfred/social-crosspost-bot
cd social-crosspost-bot
```

2. Create and configure the `.env` file:
```bash
cp .env.example .env
# Edit .env with your API credentials
```

3. Build and start the container:
```bash
docker-compose up -d
```

### Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/developerfred/social-crosspost-bot
cd social-crosspost-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API credentials
```

5. Run the bot:
```bash
python bot.py
```

## Configuration

Create a `.env` file with the following variables:

```env
# Telegram
TELEGRAM_TOKEN=your_telegram_token

# Twitter/X
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_SECRET=your_twitter_access_secret

# Bluesky
BLUESKY_EMAIL=your_bluesky_email
BLUESKY_PASSWORD=your_bluesky_password

# Farcaster
FARCASTER_MNEMONIC=your_farcaster_mnemonic
```

## Usage

1. Add the bot to your Telegram group
2. Send a message with the #topost hashtag
3. Group members can react with 👍
4. Once the message receives 7 reactions within 2 hours, it will be automatically posted to all configured platforms

### Bot Commands

- `/start` - Initialize the bot in a group

### Message Format

```
Your message content here #topost
```

## Customization

You can modify the following constants in `bot.py`:

- `REQUIRED_REACTIONS`: Number of reactions needed before posting (default: 7)
- `EXPIRATION_HOURS`: How long posts remain valid for reactions (default: 2)

## Monitoring and Maintenance

### View Logs

Using Docker:
```bash
docker-compose logs -f
```

Manual installation:
```bash
tail -f bot.log
```

### Stop the Bot

Using Docker:
```bash
docker-compose down
```

Manual installation: Use `Ctrl+C` in the terminal running the bot

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [tweepy](https://github.com/tweepy/tweepy)
- [atproto](https://github.com/bluesky-social/atproto)
- [farcaster-py](https://github.com/farcasterxyz/farcaster-py)