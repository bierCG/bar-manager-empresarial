import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%y-%m-%d %H:%M:%S",
    handlers={
        logging.FileHandler("logs/app.log", encoding="utf-8")
    }
)

logger = logging.getLogger(__name__) 