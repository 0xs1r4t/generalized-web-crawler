import asyncio
import logging
from datetime import datetime, timedelta
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn

from crawl4ai import AsyncWebCrawler
from playwright.async_api import async_playwright

from typing import List, Dict
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EcommerceCrawler:
    def __init__(self):
        self.crawler = AsyncWebCrawler()
        self.common_product_patterns = [
            "/product/",
            "/p/",
            "/item/",
            "/details/",
            "/products/",
            "/items/",
            "/goods/",
            "/detail/",
            "/buy/",
            "/shop/",
            "/pd/",
            "/goods/",
        ]
        self.requests_per_second = 2  # Adjust this value based on needs
        self.last_request_time = {}  # Track requests per domain

    async def is_product_url(self, url: str, page) -> bool:
        """Enhanced product page detection"""
        # Check URL patterns first
        lower_url = url.lower()
        if any(pattern in lower_url for pattern in self.common_product_patterns):
            return True

        try:
            # Check for common product page elements
            selectors = [
                'button[type="submit"][name="add-to-cart"]',
                "button.add-to-cart",
                "form.cart",
                "[data-product-price]",
                ".product-price",
                ".product-title",
                "div.product-details",
            ]

            for selector in selectors:
                if await page.locator(selector).count() > 0:
                    return True

            return False

        except Exception as e:
            logger.warning(f"Error checking product page elements: {str(e)}")
            return False

    async def extract_links(self, page, base_url: str) -> List[str]:
        """Extract all links from a page"""
        try:
            links = await page.evaluate(
                """() => {
                return Array.from(document.querySelectorAll('a[href]'))
                    .map(a => a.href)
                    .filter(href => href.startsWith('http'));
            }"""
            )

            # Filter and normalize URLs
            valid_links = []
            base_domain = urlparse(base_url).netloc

            for link in links:
                try:
                    parsed = urlparse(link)
                    # Only keep links from same domain
                    if parsed.netloc == base_domain:
                        valid_links.append(link)
                except Exception as e:
                    logger.warning(f"Error parsing URL {link}: {str(e)}")
                    continue

            return list(set(valid_links))  # Remove duplicates
        except Exception as e:
            logger.error(f"Error extracting links: {str(e)}")
            return []

    async def throttle_request(self, domain: str):
        """Basic rate limiting per domain"""
        now = datetime.now()
        if domain in self.last_request_time:
            time_since_last = (now - self.last_request_time[domain]).total_seconds()
            if time_since_last < (1 / self.requests_per_second):
                await asyncio.sleep((1 / self.requests_per_second) - time_since_last)
        self.last_request_time[domain] = now

    async def safe_goto(self, page, url: str, max_retries: int = 3) -> bool:
        """Attempt to load a URL with retries"""
        for attempt in range(max_retries):
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_load_state("domcontentloaded")
                return True
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(
                        f"Failed to load {url} after {max_retries} attempts: {str(e)}"
                    )
                    return False
                await asyncio.sleep(2**attempt)  # Exponential backoff
        return False

    async def crawl_domain(self, domain: str) -> Dict[str, List[str]]:
        """Crawl a single domain for product URLs"""
        base_url = f"https://{domain}"
        product_urls = set()
        visited_urls = set()

        try:
            async with async_playwright() as p:
                # Launch chromium with specific options
                browser = await p.chromium.launch(
                    headless=True,  # Run in headless mode
                    args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"],
                )

                context = await browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                )

                page = await context.new_page()

                # Start with the homepage
                logger.info(f"Starting crawl of {domain}")
                try:
                    await page.goto(base_url, wait_until="networkidle", timeout=30000)
                    await self.throttle_request(domain)  # Add rate limiting here
                    await page.wait_for_load_state("domcontentloaded")

                except Exception as e:
                    logger.error(f"Error accessing {base_url}: {str(e)}")
                    await browser.close()
                    return {"domain": domain, "product_urls": []}

                # Get initial links
                links = await self.extract_links(page, base_url)
                to_visit = set(links)

                # Basic crawling loop
                while to_visit and len(visited_urls) < 100:  # Limit for testing
                    current_url = to_visit.pop()
                    if current_url in visited_urls:
                        continue

                    visited_urls.add(current_url)
                    logger.info(f"Visiting: {current_url}")

                    try:
                        await page.goto(
                            current_url, wait_until="networkidle", timeout=30000
                        )
                        await self.throttle_request(domain)
                        await page.wait_for_load_state("domcontentloaded")

                        # Pass both URL and page to is_product_url
                        if await self.is_product_url(current_url, page):
                            product_urls.add(current_url)
                            logger.info(f"Found product URL: {current_url}")

                        # Get more links to visit
                        new_links = await self.extract_links(page, base_url)
                        to_visit.update(new_links)

                    except Exception as e:
                        logger.error(f"Error processing {current_url}: {str(e)}")
                        continue

                await browser.close()

        except Exception as e:
            logger.error(f"Error crawling {domain}: {str(e)}")

        return {"domain": domain, "product_urls": list(product_urls)}

    async def crawl_domains(self, domains: List[str]) -> List[Dict[str, List[str]]]:
        """Crawl multiple domains with progress tracking"""
        with Progress(
            SpinnerColumn(),
            *Progress.get_default_columns(),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("[cyan]Crawling domains...", total=len(domains))

            async def crawl_with_progress(domain: str):
                result = await self.crawl_domain(domain)
                progress.update(task, advance=1)
                return result

            tasks = [crawl_with_progress(domain) for domain in domains]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            valid_results = [result for result in results if isinstance(result, dict)]

            return valid_results
