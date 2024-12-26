import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime


class Logger:
    """
    A utility class for consistent logging across the project.
    """

    _instances = {}

    @staticmethod
    def get_logger(name: str, log_level: str = "INFO", log_file: str = None, max_file_size: int = 10 * 1024 * 1024, backup_count: int = 5):
        """
        Get a logger instance with a specific name.
        
        Args:
            name (str): Name of the logger, usually the module's `__name__`.
            log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            log_file (str): Path to the log file. If None, logs are sent to stdout only.
            max_file_size (int): Maximum size of the log file before rotation (default: 10MB).
            backup_count (int): Number of rotated log files to keep (default: 5).
        
        Returns:
            logging.Logger: Configured logger instance.
        """
        if name in Logger._instances:
            return Logger._instances[name]

        # Create a logger instance
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        logger.propagate = False

        # Ensure no duplicate handlers are added
        if not logger.handlers:
            # Log format
            log_format = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_format)
            logger.addHandler(console_handler)

            # File handler (optional)
            if log_file:
                # Ensure log directory exists
                os.makedirs(os.path.dirname(log_file), exist_ok=True)

                file_handler = RotatingFileHandler(
                    log_file, maxBytes=max_file_size, backupCount=backup_count
                )
                file_handler.setFormatter(log_format)
                logger.addHandler(file_handler)

        # Cache the logger instance
        Logger._instances[name] = logger
        return logger

    @staticmethod
    def clear_instances():
        """Clear the cached logger instances."""
        Logger._instances.clear()
