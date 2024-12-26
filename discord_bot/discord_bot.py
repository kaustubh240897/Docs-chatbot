import discord
import redis
from discord.ext import commands
from utils.logging import Logger
from utils.gemini import GeminiService
from utils.redis import RedisService

class DiscordBot(commands.Bot):
    def __init__(self, redis_service: RedisService, gemini_service: GeminiService, command_prefix="!"):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix=command_prefix, intents=intents)

        self.redis_service = redis_service
        self.gemini_service = gemini_service
        self.logger = Logger.get_logger(name=__name__, log_level="DEBUG", log_file="logs/discord.log")

        # Register commands (note: now explicitly using a decorator or separate definitions)
        self._register_commands()

    def _register_commands(self):
        """Registers bot commands."""
        self.remove_command("help")

        @self.command(name="help")
        async def help_command(ctx):
            """Send a help message."""
            await ctx.send("Available commands:\n!clearhistory - Clear your message history")

        @self.command(name="clearhistory")
        async def clear_history_command(ctx):
            """Clear user message history."""
            user_id = str(ctx.author.id)
            self.redis_service.clear_history(user_id)
            await ctx.send("Your message history has been cleared.")

    async def on_ready(self):
        self.logger.info(f"Bot is connected to the following servers:")
        for guild in self.guilds:
            self.logger.info(f"{guild.name} (id: {guild.id})")

    async def on_message(self, message):
        # Let commands process the message first
        await self.process_commands(message)

        # Skip bot messages
        if message.author == self.user:
            return

        # Handle DM responses
        if isinstance(message.channel, discord.DMChannel):
            user_id = str(message.author.id)
            user_history = self.redis_service.get_user_history(user_id) or []
            user_history.append(f"User: {message.content}")

            try:
                self.redis_service.trim_history(user_id)
                async with message.channel.typing():
                    bot_response = await self.gemini_service.generate_response(user_history)
                    self.redis_service.add_to_user_history(user_id, message.content, bot_response)
                    await self.send_response(message.channel, bot_response)
            except Exception as e:
                self.logger.error("Failed to generate response.", exc_info=e)
                await message.channel.send("Sorry, I couldn't access your history. Please try again later.")
        else:
            # Respond in public channels
            async with message.channel.typing():
                bot_response = await self.gemini_service.generate_response([message.content])
                await self.send_response(message.channel, bot_response)

    async def send_response(self, channel, bot_response):
        """Helper function to send responses while handling Discord's message length limit."""
        max_length = 2000
        if len(bot_response) > max_length:
            for i in range(0, len(bot_response), max_length):
                await channel.send(bot_response[i:i + max_length])
        else:
            await channel.send(bot_response)


    async def close(self):
        """Clean up resources on bot shutdown."""
        self.logger.info("Closing the bot.")
        await super().close()  # Await the close coroutine
