import redis
from utils.logging import Logger

# Redis Service for History Management
class RedisService:
    def __init__(self, redis_url):
        self.logger = Logger.get_logger(
            name=__name__,
            log_level="DEBUG",
            log_file="logs/redis.log"
        )
        self.logger.info("Connecting to Redis, with URL: %s", redis_url)
        try:
            self.client = redis.StrictRedis.from_url(redis_url, decode_responses=True, socket_timeout=10)
        except redis.ConnectionError as e:
            self.logger.error("Failed to connect to Redis.", exc_info=e)
            raise
        try:
            self.client.ping()
            self.logger.info("Redis ping successful.")
        except redis.ConnectionError as e:
            self.logger.error("Failed to ping Redis.", exc_info=e)
            raise
        
    def get_user_history(self, user_id, max_length=5):
        """Retrieve the user's message history, ensuring it doesn't exceed the maximum length."""
        try:
            history = self.client.lrange(user_id, 0, -1) or []
            return history[-max_length:]  # Return only the most recent messages
        except redis.ConnectionError as e:
            self.logger.error("Error fetching user history from Redis.", exc_info=e)
            return []
       

    def add_to_user_history(self, user_id, user_message, bot_response):
        """Add a message to the user's history in Redis."""
        try:
            self.client.rpush(user_id, f"User: {user_message}", f"Bot: {bot_response}")
        except redis.ConnectionError as e:
            self.logger.error("Error adding message to user history in Redis.", exc_info=e)

    def trim_history(self, user_id, max_length=5):
        """Trim the user's message history to the maximum length."""
        try:
            self.client.ltrim(user_id, -max_length, -1)
        except redis.ConnectionError as e:
            self.logger.error("Error trimming user history in Redis.", exc_info=e)

    def clear_history(self, user_id):
        """Clear the message history for a specific user."""
        try:
            self.client.delete(user_id)
        except redis.ConnectionError as e:
            self.logger.error("Error clearing user history in Redis.", exc_info=e)
