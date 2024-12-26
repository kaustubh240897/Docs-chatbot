import os, re
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from utils.logging import Logger
from utils.gemini import GeminiService
from utils.redis import RedisService

class SlackBot:
    """A class to encapsulate Slack bot logic, message handling, and event management."""

    def __init__(self, gemini_service: GeminiService, redis_service: RedisService, slack_bot_token, slack_signing_secret, logger=None, max_history=5):
        self.logger = logger or Logger.get_logger(
            name=__name__,
            log_level="DEBUG",
            log_file="logs/slack.log"
        )
        self.redis_service = redis_service
        self.max_history = max_history

        # Initialize Slack App
        self.app = AsyncApp(token=slack_bot_token, signing_secret=slack_signing_secret)
        self.logger.info("Slack bot initialized.")
        self.gemini_service = gemini_service

        # Register event handlers
        self._register_handlers()

    async def _set_presence(self, presence="auto"):
        try:
            await self.app.client.users_setPresence(presence=presence)
            self.logger.info(f"Presence set to {presence}.")
        except Exception as e:
            self.logger.error("Error setting presence.", exc_info=e)

    def _register_handlers(self):
        """Register Slack event handlers for the bot."""
        self.app.event("app_mention")(self._mention_event_handler)
        self.app.message(re.compile(r".*"))(self._handle_message)

    async def _mention_event_handler(self, event, say):
        """Handle @mention events in Slack."""
        self.logger.info("Bot mentioned in channel.")
        await self._handle_message(event, say)

    async def _handle_message(self, event, say):
        """Handle incoming Slack messages."""
        self.logger.info("Message received.", extra={"event": event})

        user_id = event.get("user")
        text = event.get("text")
        channel = event.get("channel")
        thread_ts = event.get("thread_ts") or event.get("ts")

        if not user_id or not text:
            self.logger.error("User ID or text is missing from the event.")
            return  # Exit if necessary information is missing

        # Retrieve and update user message history
        user_history = self.redis_service.get_user_history(user_id, max_length=self.max_history)
        user_history.append(text)


        # Prepare context for response generation
        message_history = " ".join(user_history)

        try:
            self.redis_service.trim_history(user_id, max_length=self.max_history)
            # Simulate typing by sending a typing indicator
            await say(f"Typing...", channel=channel, thread_ts=thread_ts)

            # Fetch the bot response asynchronously
            bot_response = await self.gemini_service.generate_response(message_history)

            # Update Redis with the new message
            self.redis_service.add_to_user_history(user_id, text, bot_response)

            # Add bot response to Redis
            self.redis_service.add_to_user_history(user_id, text, bot_response)

            # Split response to stay within Slack's character limit (4000 characters)
            max_length = 4000
            if len(bot_response) > max_length:
                for i in range(0, len(bot_response), max_length):
                    await say(bot_response[i:i + max_length], channel=channel, thread_ts=thread_ts)
            else:
                await say(bot_response, channel=channel, thread_ts=thread_ts)

        except Exception as e:
            self.logger.error("Error sending response to Slack.", exc_info=True, extra={"error": str(e)})
            await say("Sorry, I encountered an error while responding.", channel=channel)

    async def start(self):
        """Start the Slack bot using Socket Mode."""
        self.logger.info("Starting Slack bot...")
        handler = AsyncSocketModeHandler(self.app, os.getenv("SLACK_APP_TOKEN"))
        await handler.start_async()