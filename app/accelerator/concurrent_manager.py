import asyncio
import logging
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import List, Dict, Any, Optional, Callable
from functools import partial

logger = logging.getLogger(__name__)


class ConcurrentManager:
    def __init__(
        self,
        max_workers: Optional[int] = None,
        max_tasks: Optional[int] = None,
        batch_size: int = 32,
        use_multiprocessing: bool = True,
    ):
        # Auto-configure workers based on CPU cores
        cpu_count = multiprocessing.cpu_count()
        self.max_workers = max_workers or cpu_count
        self.max_tasks = max_tasks or (cpu_count * 2)
        self.batch_size = batch_size
        self.use_multiprocessing = use_multiprocessing

        # Initialize semaphore for concurrent tasks
        self.semaphore = asyncio.Semaphore(self.max_tasks)

        # Initialize thread pool
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.max_workers, thread_name_prefix="crawler_thread"
        )

        logger.info(
            f"Initialized ConcurrentManager with {self.max_workers} workers "
            f"({cpu_count} CPUs) and {self.max_tasks} max tasks"
        )

    async def run_in_thread(self, func: Callable, *args, **kwargs) -> Any:
        """Run a function in thread pool"""
        loop = asyncio.get_running_loop()
        if asyncio.iscoroutinefunction(func):
            # If the function is async, we need to run it in the event loop
            return await func(*args, **kwargs)
        else:
            # If it's a regular function, run it in the thread pool
            return await loop.run_in_executor(
                self.thread_pool, partial(func, *args, **kwargs)
            )

    async def process_batch_concurrent(
        self,
        items: List[Any],
        process_func: Callable,
        use_gpu: bool = True,
        chunk_size: Optional[int] = None,
    ) -> List[Any]:
        """Process items in batches with concurrency"""
        if not items:
            return []

        # Calculate optimal chunk size based on CPU cores
        if chunk_size is None:
            chunk_size = max(len(items) // (self.max_workers * 2), 1)

        results = []
        batches = [
            items[i : i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]

        async def process_batch(batch: List[Any]) -> Any:
            async with self.semaphore:
                return await self.run_in_thread(process_func, batch)

        # Process batches concurrently
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(process_batch(batch)) for batch in batches]

        for task in tasks:
            try:
                result = task.result()
                if result:
                    if isinstance(result, list):
                        results.extend(result)
                    else:
                        results.append(result)
            except Exception as e:
                logger.error(f"Error processing batch: {str(e)}")

        return results

    async def cleanup(self):
        """Cleanup resources"""
        self.thread_pool.shutdown(wait=True)
