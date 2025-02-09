import asyncio
import logging
from typing import List, Dict, Optional
from app.crawler.interfaces import ICrawlerStrategy, IURLProcessor, IBrowserManager
from app.db.repositories.product import ProductRepository
from app.db.schemas.product import ProductCreate
from app.cache.url_cache import URLCache
from app.accelerator import GPUManager, ConcurrentManager

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

        logger.info(
            f"EcommerceCrawler initialized with "
            f"workers={max_workers or 'auto'}, "
            f"tasks={max_tasks or 'auto'}, "
            f"batch_size={batch_size}, "
            f"multiprocessing={'enabled' if use_multiprocessing else 'disabled'}"
        )

    async def crawl_domains(self, domains: List[str]) -> List[Dict[str, List[str]]]:
        logger.info(f"Starting concurrent crawl for domains: {domains}")
        await self.browser_manager.setup()

        try:
            # Process each domain individually
            results = []
            for domain in domains:
                result = await self.crawl_domain(domain)
                results.append(result)

            # Process results with GPU acceleration
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
        logger.info(f"Starting crawl for domain: {domain}")
        product_urls = set()
        base_url = f"https://{domain}"

        try:
            page = await self.browser_manager.create_page()
            logger.info(f"Navigating to {base_url}")
            await page.goto(base_url)

            # Get all links on the page
            logger.info("Extracting links from page")
            links = await page.eval_on_selector_all(
                "a[href]", "elements => elements.map(el => el.href)"
            )
            logger.info(f"Found {len(links)} links on page")

            # Filter for product URLs
            for link in links:
                logger.debug(f"Checking link: {link}")
                if not await self.url_cache.is_url_cached(link):
                    if await self.url_processor.is_product_url(link):
                        logger.info(f"Found product URL: {link}")
                        product_urls.add(link)
                        await self.url_cache.cache_url(link)
                else:
                    logger.debug(f"URL already cached: {link}")

            await page.close()
            logger.info(f"Found {len(product_urls)} product URLs for {domain}")

        except Exception as e:
            logger.error(f"Error crawling {domain}: {str(e)}", exc_info=True)

        return {"domain": domain, "product_urls": list(product_urls)}
