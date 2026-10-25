import logging

from app.services.nbu import update_currency_rates

logger = logging.getLogger(__name__)


def update_all_rates() -> None:
    count = update_currency_rates()
    logger.info("Currency rates updated: %s", count)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    update_all_rates()