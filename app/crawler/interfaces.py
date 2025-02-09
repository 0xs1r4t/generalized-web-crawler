from abc import ABC, abstractmethod
from typing import List, Dict, Any


class IURLProcessor(ABC):
    @abstractmethod
    async def is_product_url(self, url: str) -> bool:
        """Check if a URL is a product URL"""
        pass


class IBrowserManager(ABC):

    @abstractmethod
    async def setup(self):
        """Setup the browser"""
        pass

    @abstractmethod
    async def cleanup(self):
        """Cleanup the browser"""
        pass

    @abstractmethod
    async def create_page(self):
        """Create a new page"""
        pass


class ICrawlerStrategy(ABC):
    @abstractmethod
    async def crawl_domain(self, domain: str) -> Dict[str, List[str]]:
        """Crawl a domain and return domains and a list of product URLs"""
        pass


class IDataExtractor(ABC):
    @abstractmethod
    async def extract_product_data(self, page, url: str) -> Dict[str, Any]:
        """Extract product details from page"""
        pass

    @abstractmethod
    async def get_selectors(self, domain: str) -> Dict[str, str]:
        """Get domain-specific selectors"""
        pass
