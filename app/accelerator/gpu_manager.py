import torch
import numpy as np
from typing import List, Any
import logging

logger = logging.getLogger(__name__)


class GPUManager:
    def __init__(self, batch_size: int = 32):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.batch_size = batch_size
        logger.info(f"Using device: {self.device}")

        if self.device.type == "cuda":
            logger.info(
                f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB"
            )

    def to_device(self, data: Any) -> torch.Tensor:
        """Move data to GPU if available"""
        if isinstance(data, np.ndarray):
            return torch.from_numpy(data).to(self.device)
        elif isinstance(data, torch.Tensor):
            return data.to(self.device)
        else:
            return torch.tensor(data).to(self.device)

    async def process_batch(self, items: List[Any]) -> np.ndarray:
        """Process a batch of items using GPU acceleration"""
        try:
            batch = self.to_device(items)

            with torch.cuda.amp.autocast():
                with torch.no_grad():
                    results = self._process(batch)

            return results.cpu().numpy()
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            raise

    def _process(self, batch: torch.Tensor) -> torch.Tensor:
        """Override this method for specific processing logic"""
        return batch
