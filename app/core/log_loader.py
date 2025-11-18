import logging
import logging.config
import os

import yaml


def setup_fallback_logging():
    """Fallback logging if _config file not found!"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)-8s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/app.log', encoding="utf-8")
        ]
    )


def setup_logging():
    """Setup Logging from YAML"""
    # Create dir if not exists
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Load YAML _config
    try:
        with open('logging_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
    except FileNotFoundError:
        print("File logging_config.yaml is not found!, using default configuration")
        setup_fallback_logging()
    except Exception as e:
        print(f"Error loading logging _config: {e}")
        setup_fallback_logging()