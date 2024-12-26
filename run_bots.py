from discord_bot.discord_bot import DiscordBot
from slack_bot.slack_bot import SlackBot
from dotenv import load_dotenv
import os, asyncio
from utils.gemini import GeminiService
from utils.logging import Logger
from utils.redis import RedisService

# Configure the main logger
logger = Logger.get_logger(
    name=__name__, 
    log_level="DEBUG", 
    log_file="logs/app.log"
)

# Load environment variables
load_dotenv()
REDIS_URL = os.getenv("REDIS_URL")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

if not REDIS_URL or not GEMINI_API_KEY or not SLACK_APP_TOKEN or not SLACK_BOT_TOKEN or not SLACK_SIGNING_SECRET or not DISCORD_BOT_TOKEN:
    logger.error("Missing environment variables. Please check your .env file.")
    exit(1)

# Initialize the Redis service
redis_service = RedisService(REDIS_URL)
# Initialize the Gemini API service
gemini_service = GeminiService(api_key=GEMINI_API_KEY)
# Initialize the Discord bot
discord_bot = DiscordBot(redis_service=redis_service, gemini_service=gemini_service)
# Initialize the Slack bot
slack_bot = SlackBot(
    gemini_service=gemini_service,
    redis_service=redis_service,
    slack_bot_token=SLACK_BOT_TOKEN,
    slack_signing_secret=SLACK_SIGNING_SECRET,
)

# Function to start the Discord bot
async def start_discord_bot():
    try:
        await discord_bot.start(token=DISCORD_BOT_TOKEN)
    except Exception as e:
        logger.error("Discord bot error", exc_info=e)

# Function to start the Slack bot
async def start_slack_bot():
    try:
        await slack_bot.start()
        await slack_bot._set_presence("auto")
    except Exception as e:
        logger.error("Slack bot error", exc_info=e)

# Main function to run both bots concurrently
async def main():
    # Run both bots as separate tasks
    try:
        await asyncio.gather(
            start_discord_bot(),
            start_slack_bot(),
        )
    except Exception as e:
        logger.error("Error occurred while running bots", exc_info=e)
        raise  # Re-raise to handle the shutdown properly

# Entry point
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bots stopped by user")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(discord_bot.close())
        loop.close()