import logging
from app.crawler.interfaces import IURLProcessor

logger = logging.getLogger(__name__)


class URLProcessor(IURLProcessor):

    def __init__(self):
        self.product_indicators = ["product", "/p/", "item", "pd", "buy"]
        self.category_indicators = ["category", "dept", "collection", "/c/"]

    async def is_product_url(self, url: str) -> bool:
        try:
            return any(
                indicator in url.lower() for indicator in self.product_indicators
            )
        except Exception as e:
            logger.error(f"Error checking product URL {url}: {str(e)}")
            return False

    async def is_category_url(self, url: str) -> bool:
        try:
            return any(
                indicator in url.lower() for indicator in self.category_indicators
            )
        except Exception as e:
            logger.error(f"Error checking category URL {url}: {str(e)}")
            return False
