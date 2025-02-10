import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.db.models.product import URLCache as URLCacheModel
from sqlalchemy import select, update

logger = logging.getLogger(__name__)


class URLCache:
    def __init__(self, db: Session):
        self.db = db
        logger.info("URLCache initialized")

    async def is_url_cached(self, url: str) -> bool:
        try:
            stmt = select(URLCacheModel).where(URLCacheModel.url == url)
            result = self.db.execute(stmt).scalar_one_or_none()
            return result is not None
        except Exception as e:
            logger.error(f"Error checking cache for URL {url}: {str(e)}")
            self.db.rollback()  # Explicitly rollback on error
            return False

    async def cache_url(self, url: str, domain: str) -> None:
        try:
            # Check if URL exists
            stmt = select(URLCacheModel).where(URLCacheModel.url == url)
            existing = self.db.execute(stmt).scalar_one_or_none()

            now = datetime.now(timezone.utc)

            if existing:
                # Update existing entry
                stmt = (
                    update(URLCacheModel)
                    .where(URLCacheModel.url == url)
                    .values(
                        domain=domain,
                        last_accessed=now,
                        access_count=URLCacheModel.access_count + 1,
                    )
                )
                self.db.execute(stmt)
            else:
                # Create new entry
                cache_entry = URLCacheModel(
                    url=url, domain=domain, first_seen=now, last_accessed=now
                )
                self.db.add(cache_entry)

            self.db.commit()
            logger.info(f"Successfully cached URL: {url}")

        except Exception as e:
            logger.error(f"Error caching URL {url}: {str(e)}")
            self.db.rollback()  # Explicitly rollback on error
            raise

    async def clear_cache(self) -> None:
        self.db.query(URLCacheModel).delete()
        self.db.commit()
