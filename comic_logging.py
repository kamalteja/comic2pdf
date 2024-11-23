""" Custom logger """

import logging
import os

# Define a custom log level for TMI
TMI_LOG_LEVEL = 5  # Lower than DEBUG (which is 10)
logging.addLevelName(TMI_LOG_LEVEL, "TMI")


# Create a custom function for logging at the TMI level
def tmi(l, message, *args, **kwargs):
    """Log 'message % args' with severity 'TMI'"""
    if l.isEnabledFor(TMI_LOG_LEVEL):
        l.log(TMI_LOG_LEVEL, message, *args, **kwargs)


# Add the function to the logging module's Logger class
logging.Logger.tmi = tmi


def get_logger(name: str):
    """Create a custom logger"""
    logger = logging.getLogger(name)

    # Set the log level from the environment variable or default to INFO
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    logger.setLevel(log_level)

    # Create a console handler and set the level
    handler = logging.StreamHandler()
    handler.setLevel(log_level)

    # Create a formatter and set it for the handler
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    return logger
