import asyncio
import logging
from app.bot import main

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info('Бот остановлен')