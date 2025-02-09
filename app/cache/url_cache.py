import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.db.models.product import URLCache as URLCacheModel

logger = logging.getLogger(__name__)


class URLCache:
    def __init__(self, db: Session):
        self.db = db
        logger.info("URLCache initialized")

    async def is_url_cached(self, url: str) -> bool:
        try:
            cache_entry = (
                self.db.query(URLCacheModel).filter(URLCacheModel.url == url).first()
            )
            if cache_entry:
                logger.debug(f"Cache hit for URL: {url}")
                cache_entry.last_accessed = datetime.now(timezone.utc)
                cache_entry.access_count += 1
                self.db.commit()
                return True
            logger.debug(f"Cache miss for URL: {url}")
            return False
        except Exception as e:
            logger.error(f"Error checking cache for URL {url}: {str(e)}")
            return False

    async def cache_url(self, url: str) -> None:
        try:
            logger.debug(f"Caching URL: {url}")
            cache_entry = URLCacheModel(
                url=url,
                first_seen=datetime.now(timezone.utc),
                last_accessed=datetime.now(timezone.utc),
            )
            self.db.add(cache_entry)
            self.db.commit()
            logger.info(f"Successfully cached URL: {url}")
        except Exception as e:
            logger.error(f"Error caching URL {url}: {str(e)}")
            raise

    async def clear_cache(self) -> None:
        self.db.query(URLCacheModel).delete()
        self.db.commit()
