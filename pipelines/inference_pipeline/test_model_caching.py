#!/usr/bin/env python3
"""
Test script to demonstrate the model caching functionality.
"""

import logging
import time
from pathlib import Path

from inference_pipeline import constants
from inference_pipeline.langchain_bot import FinancialBot
from inference_pipeline.models import get_model_registry_stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """
    Main function to test model caching.
    """
    # Create a financial bot with preloading enabled
    logger.info("Creating first bot instance with preloading enabled")
    start_time = time.time()
    bot1 = FinancialBot(
        preload_default_model=True,
        streaming=False,
    )
    logger.info(f"First bot creation took {time.time() - start_time:.2f} seconds")
    
    # Get a response from the first bot
    logger.info("Getting response from first bot")
    start_time = time.time()
    response1 = bot1.answer(
        about_me="I am a financial analyst interested in tech stocks.",
        question="What are the latest trends in AI technology stocks?",
    )
    logger.info(f"First bot response took {time.time() - start_time:.2f} seconds")
    logger.info(f"Response: {response1[:100]}...")
    
    # Create a second bot instance - this should reuse the cached model
    logger.info("Creating second bot instance - should use cached model")
    start_time = time.time()
    bot2 = FinancialBot(
        preload_default_model=False,  # No need to preload as model should be cached
        streaming=False,
    )
    logger.info(f"Second bot creation took {time.time() - start_time:.2f} seconds")
    
    # Get a response from the second bot
    logger.info("Getting response from second bot")
    start_time = time.time()
    response2 = bot2.answer(
        about_me="I am an investor looking at the energy sector.",
        question="What are the prospects for renewable energy stocks?",
    )
    logger.info(f"Second bot response took {time.time() - start_time:.2f} seconds")
    logger.info(f"Response: {response2[:100]}...")
    
    # Print model registry stats
    logger.info(f"Model registry stats: {get_model_registry_stats()}")

if __name__ == "__main__":
    main()
