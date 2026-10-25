import logging

from app.services.coingecko import update_crypto_rates
from app.services.metals import update_metal_rates
from app.services.nbu import update_currency_rates
from app.services.news import update_news
logger = logging.getLogger(__name__)

def update_news_job() -> None:
    """Новини: кожні 30 хв.""""
    _run("news", update_news)
    
def _run(name: str, func) -> None:
    try:
        logger.info("%s rates updated: %s", name, func())
    except Exception:
        logger.exception("%s rates update failed", name)


def update_fast_rates() -> None:
    """Валюти та крипта: кожні 10 хв."""
    _run("currency", update_currency_rates)
    _run("crypto", update_crypto_rates)


def update_metals() -> None:
    """Метали: раз на годину."""
    _run("metals", update_metal_rates)


def update_all_rates() -> None:
    update_fast_rates()
    update_metals()
    update_news_job()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    update_all_rates()