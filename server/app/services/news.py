import html
import logging
import re
from datetime import datetime, timezone
from time import mktime

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.news import News, NewsCategory

logger = logging.getLogger(__name__)

# (url, назва джерела, категорія за замовчуванням)
FEEDS = [
    ("https://www.epravda.com.ua/rss/", "Економічна правда", NewsCategory.ECONOMY),
    ("https://cointelegraph.com/rss", "Cointelegraph", NewsCategory.CRYPTO),
]

CURRENCY_WORDS = (
    "курс", "долар", "євро", "гривн", "валют", "нбу", "обмін",
    "dollar", "euro", "forex", "currency",
)
CRYPTO_WORDS = (
    "біткоїн", "біткойн", "крипт", "ethereum", "ефіріум", "bitcoin", "crypto",
    "blockchain", "блокчейн", "binance", "btc", "eth",
)

MAX_PER_FEED = 30
TAG_RE = re.compile(r"<[^>]+>")


def clean_text(text: str) -> str:
    text = html.unescape(TAG_RE.sub(" ", text or ""))
    return " ".join(text.split())


def short_summary(text: str, limit: int = 300) -> str:
    text = clean_text(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def detect_category(title: str, default: NewsCategory) -> NewsCategory:
    lowered = title.lower()
    if any(word in lowered for word in CRYPTO_WORDS):
        return NewsCategory.CRYPTO
    if any(word in lowered for word in CURRENCY_WORDS):
        return NewsCategory.CURRENCY
    return default


def extract_image(entry) -> str | None:
    for media in entry.get("media_content", []) or []:
        if media.get("url"):
            return media["url"]
    for enclosure in entry.get("enclosures", []) or []:
        if str(enclosure.get("type", "")).startswith("image") and enclosure.get("href"):
            return enclosure["href"]
    return None


def parse_date(entry) -> datetime:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        return datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)
    return datetime.now(timezone.utc)


def fetch_feed(url: str) -> list:
    last_error = None
    for attempt in (1, 2):
        try:
            response = httpx.get(
                url, timeout=15, follow_redirects=True,
                headers={"User-Agent": "FinPulse/1.0"},
            )
            response.raise_for_status()
            return feedparser.parse(response.content).entries
        except httpx.HTTPError as exc:
            last_error = exc
            logger.warning("RSS %s failed (attempt %s): %s", url, attempt, exc)
    raise RuntimeError(f"RSS unavailable: {url}") from last_error


def update_news(db: Session | None = None) -> int:
    own_session = db is None
    db = db or SessionLocal()
    added = 0
    try:
        for url, source_name, default_category in FEEDS:
            try:
                entries = fetch_feed(url)[:MAX_PER_FEED]
            except RuntimeError:
                logger.error("%s skipped, keeping previous news", source_name)
                continue

            links = [e.get("link") for e in entries if e.get("link")]
            known = set(db.scalars(select(News.source_url).where(News.source_url.in_(links))))

            for entry in entries:
                link = entry.get("link")
                title = clean_text(entry.get("title", ""))
                if not link or not title or link in known:
                    continue
                known.add(link)
                db.add(
                    News(
                        title=title[:500],
                        summary=short_summary(entry.get("summary", "")),
                        category=detect_category(title, default_category),
                        source_url=link[:1000],
                        source_name=source_name,
                        image_url=extract_image(entry),
                        published_at=parse_date(entry),
                    )
                )
                added += 1

        db.commit()
        return added
    except Exception:
        db.rollback()
        raise
    finally:
        if own_session:
            db.close()
