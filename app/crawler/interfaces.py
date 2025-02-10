from abc import ABC, abstractmethod
from typing import List, Dict, Any, Set


class IURLProcessor(ABC):
    @abstractmethod
    async def is_product_url(self, url: str) -> bool:
        """Check if a URL is a product URL"""
        pass

    @abstractmethod
    async def is_category_url(self, url: str) -> bool:
        """Check if a URL is a category/collection URL"""
        pass

    @abstractmethod
    async def normalize_url(self, url: str, base_domain: str) -> str:
        """Normalize URL to full path with domain"""
        pass

    @abstractmethod
    async def extract_urls_from_page(self, page: Any) -> Set[str]:
        """Extract all URLs from a page"""
        pass

    @abstractmethod
    async def filter_urls(self, urls: Set[str], domain: str) -> Dict[str, Set[str]]:
        """Filter URLs into categories and products"""
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
