from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from app.db.session import get_main_db, get_cache_db
from app.db.repositories.product import ProductRepository
from app.crawler.base import EcommerceCrawler
from app.crawler.url_processor import URLProcessor
from app.crawler.browser_manager import PlaywrightManager
from app.cache.url_cache import URLCache

router = APIRouter(prefix="/api/v1/crawler", tags=["crawler"])


@router.post("/crawl")
async def crawl_domains(
    domains: List[str],
    max_workers: Optional[int] = Query(
        None, description="Number of worker processes (default: CPU count)"
    ),
    max_tasks: Optional[int] = Query(
        None, description="Maximum concurrent tasks (default: CPU count * 2)"
    ),
    batch_size: int = Query(32, description="Batch size for processing"),
    use_multiprocessing: bool = Query(True, description="Enable multiprocessing"),
    main_db: Session = Depends(get_main_db),
    cache_db: Session = Depends(get_cache_db),
):
    crawler = EcommerceCrawler(
        url_processor=URLProcessor(),
        browser_manager=PlaywrightManager(),
        product_repo=ProductRepository(main_db),
        url_cache=URLCache(cache_db),
        max_workers=max_workers,
        max_tasks=max_tasks,
        batch_size=batch_size,
        use_multiprocessing=use_multiprocessing,
    )

    return await crawler.crawl_domains(domains)
