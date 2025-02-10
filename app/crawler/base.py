import asyncio
import logging
import time
from typing import List, Dict, Optional
from app.crawler.interfaces import ICrawlerStrategy, IURLProcessor, IBrowserManager
from app.db.repositories.product import ProductRepository
from app.db.schemas.product import ProductCreate
from app.cache.url_cache import URLCache
from app.accelerator import GPUManager, ConcurrentManager
from collections import deque
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class EcommerceCrawler(ICrawlerStrategy):
    def __init__(
        self,
        url_processor: IURLProcessor,
        browser_manager: IBrowserManager,
        product_repo: ProductRepository,
        url_cache: URLCache,
        max_workers: Optional[int] = None,
        max_tasks: Optional[int] = None,
        batch_size: int = 32,
        use_multiprocessing: bool = True,
    ):
        self.url_processor = url_processor
        self.browser_manager = browser_manager
        self.product_repo = product_repo
        self.url_cache = url_cache

        # Initialize managers with configurable parameters
        self.gpu_manager = GPUManager(batch_size=batch_size)
        self.concurrent_manager = ConcurrentManager(
            max_workers=max_workers,
            max_tasks=max_tasks,
            batch_size=batch_size,
            use_multiprocessing=use_multiprocessing,
        )

        # Add default headers
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }

        logger.info(
            f"EcommerceCrawler initialized with "
            f"workers={max_workers or 'auto'}, "
            f"tasks={max_tasks or 'auto'}, "
            f"batch_size={batch_size}, "
            f"multiprocessing={'enabled' if use_multiprocessing else 'disabled'}"
        )

        self.domain_queues = {}  # Track queues per domain
        self.domain_last_request = {}  # Track last request time per domain
        self.politeness_delay = 1.0  # Delay between requests to same domain

    async def crawl_domains(self, domains: List[str]) -> List[Dict[str, List[str]]]:
        logger.info(f"Starting concurrent crawl for domains: {domains}")
        await self.browser_manager.setup()

        try:
            # Create tasks for all domains concurrently
            async with asyncio.TaskGroup() as tg:
                tasks = [
                    tg.create_task(self.crawl_domain(domain)) for domain in domains
                ]

            results = [t.result() for t in tasks]
            processed_results = await self._process_results(results)
            return processed_results

        finally:
            await self.browser_manager.cleanup()
            await self.concurrent_manager.cleanup()

    async def _process_results(
        self, results: List[Dict[str, List[str]]]
    ) -> List[Dict[str, List[str]]]:
        """Process and save results using both GPU and CPU cores"""
        processed_results = []

        for result in results:
            domain = result["domain"]
            urls = result["product_urls"]

            # Process URLs in parallel using both GPU and CPU
            processed_urls = await self.concurrent_manager.process_batch_concurrent(
                items=urls,
                process_func=self._process_url,
                use_gpu=True,
                chunk_size=self.concurrent_manager.batch_size,
            )

            processed_results.append({"domain": domain, "product_urls": processed_urls})

        return processed_results

    async def _process_url(self, url: str) -> Optional[str]:
        """Process individual URL with error handling"""
        try:
            # Add your URL processing logic here
            return url
        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            return None

    async def crawl_domain(self, domain: str) -> Dict[str, List[str]]:
        logger.info(f"Starting BFS crawl for domain: {domain}")
        product_urls = set()
        visited_urls = set()
        queue = deque([(f"https://{domain}", 0)])
        max_depth = 2

        while queue:
            await self._respect_rate_limit(domain)

            current_url, depth = queue.popleft()
            if depth > max_depth or current_url in visited_urls:
                continue

            visited_urls.add(current_url)
            logger.info(f"Processing {current_url} at depth {depth}")

            try:
                page = await self.browser_manager.create_page()
                await page.set_extra_http_headers(self.headers)
                await page.goto(current_url, timeout=45000)

                urls = await self.url_processor.extract_urls_from_page(page)
                filtered_urls = await self.url_processor.filter_urls(urls, domain)

                # Process product URLs - add additional checks
                for url in filtered_urls["products"]:
                    normalized_url = await self.url_processor.normalize_url(url, domain)
                    # Skip pagination and category-like URLs
                    if any(
                        pattern in normalized_url.lower()
                        for pattern in [
                            "/shop/",
                            "/category/",
                            "/page/",
                            "?p=",
                            "page=",
                            "/products/",  # general products listing
                            "/collections/",
                        ]
                    ):
                        logger.debug(f"Skipping non-product URL: {normalized_url}")
                        continue

                    if await self.url_processor.is_product_url(normalized_url):
                        logger.info(f"Found product URL: {normalized_url}")
                        product_urls.add(normalized_url)
                        await self.url_cache.cache_url(normalized_url, domain)
                        await self._add_product_to_db(normalized_url, domain)

                # Process category URLs
                for url in filtered_urls["categories"]:
                    normalized_url = await self.url_processor.normalize_url(url, domain)
                    if url not in visited_urls:
                        queue.append((normalized_url, depth + 1))
                        await self.url_cache.cache_url(normalized_url, domain)

                await page.close()

            except Exception as e:
                logger.error(f"Error processing {current_url}: {str(e)}")
                continue

            self.domain_last_request[domain] = time.time()

        logger.info(f"Found {len(product_urls)} product URLs for {domain}")
        return {"domain": domain, "product_urls": list(product_urls)}

    async def _add_product_to_db(self, url: str, domain: str):
        """Add product URL to products table"""
        try:
            # Check if product already exists
            existing_product = await self.product_repo.get_product_by_url(url)
            if existing_product:
                logger.info(f"Product already exists in database: {url}")
                return existing_product

            # Create product entry using the ProductCreate schema
            product_data = ProductCreate(
                url=url,
                domain=domain,
                status="pending",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            # Add to database
            new_product = await self.product_repo.create_product(product_data)
            logger.info(f"Added product to database: {url}")
            return new_product

        except Exception as e:
            logger.error(f"Error adding product to database {url}: {str(e)}")
            # Ensure session is rolled back on error
            await self.product_repo.rollback()

    async def _respect_rate_limit(self, domain: str) -> None:
        """Ensure politeness delay between requests to same domain"""
        last_request = self.domain_last_request.get(domain, 0)
        now = time.time()
        delay = max(
            last_request + self.politeness_delay - now, 2.0
        )  # Minimum 2 second delay
        if delay > 0:
            await asyncio.sleep(delay)
