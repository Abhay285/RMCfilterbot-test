import asyncio
import logging
from Client import bot
from utils.Helpers import create_indexes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

async def main():
    # Create database indexes
    await create_indexes()
    
    # Start the bot
    await bot.start()
    logger.info("RMC Bot Started Successfully!")
    
    # Get bot info
    me = await bot.get_me()
    logger.info(f"Bot ID: {me.id}, Username: @{me.username}")
    
    # Run indefinitely
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
