from core.database import Base, engine
from utils.logger import logger


def main() -> None:
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema ensured.")


if __name__ == "__main__":
    main()
