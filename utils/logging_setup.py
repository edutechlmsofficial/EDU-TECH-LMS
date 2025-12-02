import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(app):
    # Skip file logging if there are permission issues
    app.logger.setLevel(logging.INFO)
    # Use console logging only to avoid file locking issues
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    console_handler.setLevel(logging.INFO)
    app.logger.addHandler(console_handler)
    app.logger.info('EduTechApp startup')
