import logging
from urllib.parse import urlparse, urljoin
from typing import Set, Dict, Any
from app.crawler.interfaces import IURLProcessor
import re

logger = logging.getLogger(__name__)


class URLProcessor(IURLProcessor):

    def __init__(self):
        # URL pattern indicators
        self.product_indicators = [
            "product",
            "/p/",
            "item",
            "detail",
            "pd",
            "buy",
            "shop",
            "/i/",
            "goods",
            # Add more specific patterns
            r"/p/\d+",
            r"/product/\d+",
            r"/item/\d+",
            r"/pd/\d+",
        ]
        self.category_indicators = [
            "category",
            "dept",
            "collection",
            "/c/",
            "catalog",
            "products",
            "shop",
            "list",
            "browse",
            "cat",
            "section",
        ]
        # URLs to ignore
        self.excluded_patterns = [
            "login",
            "cart",
            "checkout",
            "account",
            "wishlist",
            "search",
            "contact",
            "about",
            "policy",
            "terms",
            "help",
            "support",
            "javascript:",
            "mailto:",
            "tel:",
        ]

    async def is_product_url(self, url: str) -> bool:
        """Enhanced product URL detection"""
        url_lower = url.lower()

        # Check for exact patterns first
        for pattern in self.product_indicators:
            if pattern.startswith("r/"):
                # Regex pattern
                if re.search(pattern[2:], url_lower):
                    return True
            elif pattern in url_lower:
                return True

        # Additional checks for common product URL patterns
        parts = urlparse(url_lower).path.split("/")
        if any(part.startswith(("p-", "prod-", "item-")) for part in parts):
            return True

        return False

    async def is_category_url(self, url: str) -> bool:
        """Check if URL matches category patterns"""
        url_lower = url.lower()
        return any(
            indicator in url_lower for indicator in self.category_indicators
        ) and not any(excluded in url_lower for excluded in self.excluded_patterns)

    async def normalize_url(self, url: str, base_domain: str) -> str:
        """Normalize URL to full path with domain"""
        try:
            # Parse the URL
            parsed = urlparse(url)

            # If no scheme, add https://
            if not parsed.scheme:
                url = f"https://{url}"

            # If relative path, join with base domain
            if not parsed.netloc:
                url = urljoin(f"https://{base_domain}", url)

            # Remove fragments and clean up
            cleaned_url = url.split("#")[0].rstrip("/")
            return cleaned_url
        except Exception as e:
            logger.error(f"Error normalizing URL {url}: {str(e)}")
            return url

    async def extract_urls_from_page(self, page: Any) -> Set[str]:
        """Extract all URLs from a page"""
        try:
            # Get all links
            links = await page.eval_on_selector_all(
                "a[href]", "elements => elements.map(el => el.href)"
            )

            # Additional selectors for potential AJAX-loaded content
            more_links = await page.eval_on_selector_all(
                "[data-url], [data-href]",
                """elements => elements.map(el => 
                    el.getAttribute('data-url') || 
                    el.getAttribute('data-href')
                )""",
            )

            # Combine and filter unique URLs
            all_links = set(links + more_links)
            return {link for link in all_links if link and isinstance(link, str)}

        except Exception as e:
            logger.error(f"Error extracting URLs from page: {str(e)}")
            return set()

    async def filter_urls(self, urls: Set[str], domain: str) -> Dict[str, Set[str]]:
        """Filter URLs into categories and products"""
        products = set()
        categories = set()

        for url in urls:
            # Normalize URL first
            normalized_url = await self.normalize_url(url, domain)

            # Skip URLs from different domains
            if domain not in normalized_url:
                continue

            # Categorize URL
            if await self.is_product_url(normalized_url):
                products.add(normalized_url)
            elif await self.is_category_url(normalized_url):
                categories.add(normalized_url)

        return {"products": products, "categories": categories}
