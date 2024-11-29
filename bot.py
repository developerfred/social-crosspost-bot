import logging
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from atproto import Client as AtprotoClient
from tweepy import Client as TwitterClient
import os
from farcaster import Warpcast
import asyncio
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
import nest_asyncio
from requests.auth import AuthBase
from requests_oauthlib import OAuth1Session
import json
import base64
import tweepy

class TwitterOAuth2:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expiry = None
        self.logger = logging.getLogger(__name__)

    def _refresh_token(self) -> None:
        auth_url = "https://api.twitter.com/2/oauth2/token"
        auth_str = f"{self.client_id}:{self.client_secret}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {b64_auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "client_credentials",
            "scope": "tweet.read tweet.write users.read",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(auth_url, headers=headers, data=data)
            
            if response.status_code != 200:
                self.logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                raise Exception(f"Token refresh failed: {response.text}")
                
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.token_expiry = datetime.now() + timedelta(seconds=token_data.get('expires_in', 7200))
            self.logger.info("Successfully obtained access token")
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error during token refresh: {str(e)}")
            raise

    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers, refreshing token if needed"""
        if not self.access_token or datetime.now() >= self.token_expiry:
            self._refresh_token()
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

class TwitterAPI:
    """Twitter API v2 client with improved error handling and pagination support"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.auth = TwitterOAuth2(client_id, client_secret)
        self.logger = logging.getLogger(__name__)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to Twitter API with error handling"""
        url = f"{self.base_url}/{endpoint}"
        headers = self.auth.get_headers()
        
        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {str(e)}")
            raise

    def create_tweet(self, text: str) -> Dict[str, Any]:
        url = "https://api.twitter.com/2/tweets"
        headers = self.auth.get_headers()
        payload = {"text": text}
        
        try:
            self.logger.debug(f"Sending tweet with payload: {payload}")
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code != 201:
                self.logger.error(f"Tweet creation failed with status {response.status_code}: {response.text}")
                raise Exception(f"Tweet creation failed: {response.text}")
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error during tweet creation: {str(e)}")
            raise

    def upload_media(self, media_file) -> str:
        """Upload media and return media ID"""
        upload_url = "https://upload.twitter.com/1.1/media/upload.json"
        headers = self.auth.get_headers()
        
        try:
            response = requests.post(upload_url, headers=headers, files={"media": media_file})
            response.raise_for_status()
            return response.json()["media_id_string"]
        except requests.exceptions.RequestException as e:
            logging.error(f"Media upload failed: {str(e)}")
            raise

    def search_tweets(self, query: str, max_results: int = 10, 
                     tweet_fields: Optional[List[str]] = None,
                     expansions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Search tweets with pagination support"""
        params = {
            "query": query,
            "max_results": max_results
        }
        
        if tweet_fields:
            params["tweet.fields"] = ",".join(tweet_fields)
        if expansions:
            params["expansions"] = ",".join(expansions)
            
        return self._make_request("GET", "tweets/search/recent", params=params)

    def get_user_tweets(self, user_id: str, max_results: int = 100,
                       tweet_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get tweets from a specific user"""
        params = {"max_results": max_results}
        if tweet_fields:
            params["tweet.fields"] = ",".join(tweet_fields)
            
        return self._make_request("GET", f"users/{user_id}/tweets", params=params)

    def get_tweet_metrics(self, tweet_id: str) -> Dict[str, Any]:
        """Get engagement metrics for a tweet"""
        fields = ["public_metrics", "non_public_metrics", "organic_metrics"]
        return self._make_request("GET", f"tweets/{tweet_id}", 
                                params={"tweet.fields": ",".join(fields)})

# Enable nested event loops
nest_asyncio.apply()

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Platform enable/disable flags
PLATFORMS_CONFIG = {
    'twitter': False,
    'bluesky': False,
    'farcaster': False
}

# API credentials configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
BLUESKY_EMAIL = os.getenv("BLUESKY_EMAIL")
BLUESKY_PASSWORD = os.getenv("BLUESKY_PASSWORD")
FARCASTER_MNEMONIC = os.getenv("FARCASTER_MNEMONIC")
TWITTER_CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
TWITTER_CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")

# Global constants
REQUIRED_REACTIONS = 1
EXPIRATION_HOURS = 2

class CrossPostBot:
    def __init__(self, loop=None):
        self.tracked_messages: Dict[int, Dict] = {}
        self.posted_messages: Set[int] = set()
        self.reaction_messages: Dict[int, int] = {}
        self.loop = loop or asyncio.get_event_loop()
        
        # Initialize platforms
        self._initialize_platforms()

    def _initialize_platforms(self):
        """Initialize social media platform clients"""
        if PLATFORMS_CONFIG['twitter']:
            self.twitter = tweepy.Client(
                bearer_token=TWITTER_BEARER_TOKEN,
                consumer_key=TWITTER_API_KEY,
                consumer_secret=TWITTER_API_SECRET,
                access_token=TWITTER_ACCESS_TOKEN,
                access_token_secret=TWITTER_ACCESS_SECRET,
                wait_on_rate_limit=True
            )
        else:
            self.twitter = None
            
        if PLATFORMS_CONFIG['bluesky']:
            self.bluesky = AtprotoClient()
            self.bluesky.login(BLUESKY_EMAIL, BLUESKY_PASSWORD)
        else:
            self.bluesky = None
            
        if PLATFORMS_CONFIG['farcaster']:
            try:
                self.client = Warpcast(mnemonic=FARCASTER_MNEMONIC)
                health_check = self.client.get_healthcheck()
                logger.info(f"Farcaster connection status: {health_check}")
            except Exception as e:
                logger.error(f"Failed to initialize Farcaster client: {str(e)}")
                self.client = None
        else:
            self.client = None

    async def notify_group(self, chat_id: int, message: str, context: ContextTypes.DEFAULT_TYPE):
        """Send notification to the group"""
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for the /start command"""
        await update.message.reply_text(
            'Bot initialized! Monitoring messages with #topost tag'
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process new messages and add reaction buttons"""
        if not update.message or not update.message.text:
            return
            
        if "#topost" not in update.message.text:
            return
            
        message = update.message
        keyboard = [[InlineKeyboardButton("👍", callback_data="like")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        sent_message = await message.reply_text(
            "React with 👍 to crosspost",
            reply_markup=reply_markup
        )
            
        message_data = {
            'message_id': message.message_id,
            'chat_id': message.chat_id,
            'text': message.text.replace("#topost", "").strip(),
            'media': None,
            'reactions': set(),  # Store user IDs who reacted
            'timestamp': datetime.now(),
            'posted': False
        }
        
        if message.photo:
            message_data['media'] = {
                'type': 'photo',
                'file_id': message.photo[-1].file_id
            }
        elif message.video:
            message_data['media'] = {
                'type': 'video',
                'file_id': message.video.file_id
            }
        elif message.animation:
            message_data['media'] = {
                'type': 'animation',
                'file_id': message.animation.file_id
            }
            
        self.tracked_messages[message.message_id] = message_data
        self.reaction_messages[sent_message.message_id] = message.message_id
        logger.info(f"New message tracked: {message_data['message_id']}")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle reaction button callbacks"""
        query = update.callback_query
        await query.answer()
        
        reaction_msg_id = query.message.message_id
        if reaction_msg_id not in self.reaction_messages:
            return
            
        original_msg_id = self.reaction_messages[reaction_msg_id]
        message_data = self.tracked_messages[original_msg_id]
        
        # Add user to reactions if not already reacted
        user_id = query.from_user.id
        if user_id not in message_data['reactions']:
            message_data['reactions'].add(user_id)
            
            reaction_count = len(message_data['reactions'])
            remaining = REQUIRED_REACTIONS - reaction_count
            
            if remaining > 0:
                await query.message.edit_text(
                    f"React with 👍 to crosspost\nNeeded: {remaining} more reactions",
                    reply_markup=query.message.reply_markup
                )
            
            logger.info(f"New reaction on message {original_msg_id}. Total: {reaction_count}")
            
            if (reaction_count >= REQUIRED_REACTIONS and 
                not message_data['posted'] and 
                original_msg_id not in self.posted_messages):
                
                time_diff = datetime.now() - message_data['timestamp']
                if time_diff <= timedelta(hours=EXPIRATION_HOURS):
                    await self.cross_post(message_data, context)
                    message_data['posted'] = True
                    self.posted_messages.add(original_msg_id)
                    await query.message.edit_text("Message has been cross-posted! ✅")

    async def cross_post(self, message_data: Dict, context: ContextTypes.DEFAULT_TYPE):
        """Distribute content across enabled social media platforms"""
        chat_id = message_data['chat_id']
        platforms_status = []
        
        try:
            media_file = None
            if message_data['media']:
                media_file = await context.bot.get_file(message_data['media']['file_id'])
            
            await self.notify_group(chat_id, "🚀 Initiating crosspost to platforms...", context)
                
            if PLATFORMS_CONFIG['farcaster'] and self.client:
                try:
                    if media_file:
                        self.client.post_cast(text=message_data['text'], media=media_file)
                    else:
                        self.client.post_cast(text=message_data['text'])
                    platforms_status.append("✅ Farcaster: Successfully posted")
                except Exception as e:
                    error_msg = str(e)[:100]  # Limit error length
                    platforms_status.append(f"❌ Farcaster: Error - {error_msg}")
                    logger.error(f"Failed to post to Farcaster: {str(e)}")

            if PLATFORMS_CONFIG['twitter'] and self.twitter:
                try:
                    media_ids = None
                    if media_file:
                        auth = tweepy.OAuth1UserHandler(
                            TWITTER_API_KEY, 
                            TWITTER_API_SECRET,
                            TWITTER_ACCESS_TOKEN, 
                            TWITTER_ACCESS_SECRET
                        )
                        api = tweepy.API(auth)
                        media = api.media_upload(filename="media", file=media_file)
                        media_ids = [media.media_id]
                    
                    response = self.twitter.create_tweet(
                        text=message_data['text'],
                        media_ids=media_ids
                    )
                    platforms_status.append("✅ Twitter: Successfully posted")
                except Exception as e:
                    error_msg = str(e)[:100]
                    platforms_status.append(f"❌ Twitter: Error - {error_msg}")
                    logger.error(f"Failed to post to Twitter: {str(e)}")
                    
            if PLATFORMS_CONFIG['bluesky'] and self.bluesky:
                try:
                    if media_file:
                        self.bluesky.post_with_media(message_data['text'], media_file)
                    else:
                        self.bluesky.post(message_data['text'])
                    platforms_status.append("✅ Bluesky: Successfully posted")
                except Exception as e:
                    error_msg = str(e)[:100]
                    platforms_status.append(f"❌ Bluesky: Error - {error_msg}")
            
            # Send final report
            status_report = "\n".join(platforms_status)
            final_report = f"📊 Crosspost Report:\n\n{status_report}"
            await self.notify_group(chat_id, final_report, context)
            
        except Exception as e:
            error_msg = f"❌ General crosspost error: {str(e)[:100]}"
            await self.notify_group(chat_id, error_msg, context)
            logger.error(f"Failed to cross-post message {message_data['message_id']}: {str(e)}")

    async def cleanup_expired(self):
        """Remove expired messages from tracking"""
        while True:
            current_time = datetime.now()
            expired_messages = []
            
            for message_id, data in self.tracked_messages.items():
                time_diff = current_time - data['timestamp']
                if time_diff > timedelta(hours=EXPIRATION_HOURS):
                    expired_messages.append(message_id)
                    
            for message_id in expired_messages:
                # Clean up reaction messages mapping
                for reaction_id, orig_id in list(self.reaction_messages.items()):
                    if orig_id == message_id:
                        del self.reaction_messages[reaction_id]
                del self.tracked_messages[message_id]
                logger.info(f"Removed expired message: {message_id}")
                
            await asyncio.sleep(300)  # Check every 5 minutes


def run_bot():
    """Run the bot with proper event loop handling"""
    try:
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Initialize bot with the loop
        bot = CrossPostBot(loop=loop)
        
        # Create application
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
        application.add_handler(CallbackQueryHandler(bot.handle_callback))
        
        # Start cleanup task
        loop.create_task(bot.cleanup_expired())
        
        # Start polling
        logger.info("Bot starting up...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Error running bot: {str(e)}")
        raise
    finally:
        loop.close()

if __name__ == '__main__':
    run_bot()