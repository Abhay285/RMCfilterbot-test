import asyncio
import logging
from Client import bot
from utils.Helpers import create_indexes

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

async def main():
    await create_indexes()
    logger.info("Database initialized")
    
    await bot.start()
    logger.info("Bot started successfully")
    
    me = await bot.get_me()
    logger.info(f"Bot ID: {me.id} | Username: @{me.username}")
    
    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
