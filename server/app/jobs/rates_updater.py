import logging

from app.services.coingecko import update_crypto_rates
from app.services.nbu import update_currency_rates

logger = logging.getLogger(__name__)


def update_all_rates() -> None:
    for name, func in (
        ("currency", update_currency_rates),
        ("crypto", update_crypto_rates),
    ):
        try:
            count = func()
            logger.info("%s rates updated: %s", name, count)
        except Exception:
            logger.exception("%s rates update failed", name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    update_all_rates()