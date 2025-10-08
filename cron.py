#!/usr/bin/env python3
"""
Railway Cron Script for Newsletter Generation
This script runs when Railway cron schedule triggers
"""

import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main cron function"""
    logger.info("🕐 Railway cron script started")
    
    # Import the newsletter generation function
    try:
        from app import run_cron_generation
        
        # Run newsletter generation
        success = run_cron_generation()
        
        if success:
            logger.info("✅ Cron newsletter generation completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Cron newsletter generation failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Cron script error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
