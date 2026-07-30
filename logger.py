import json
import aiofiles
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

class JSONLLogger:
    """Writes JSON Lines (one JSON object per line) to a file."""
    
    def __init__(self, log_dir: str = "logs", run_name: Optional[str] = None):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if run_name:
            self.log_file = self.log_dir / f"{run_name}_{timestamp}.jsonl"
        else:
            self.log_file = self.log_dir / f"run_{timestamp}.jsonl"
        
        self._file = None
        self._is_closed = False
    
    async def __aenter__(self):
        self._file = await aiofiles.open(self.log_file, "a")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._file:
            await self._file.close()
        self._is_closed = True
    
    async def log(self, event: str, data: Dict[str, Any]):
        """Write a single JSONL line."""
        if self._is_closed or not self._file:
            return
        
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event": event,
            **data
        }
        
        try:
            await self._file.write(json.dumps(entry, ensure_ascii=False) + "\n")
            await self._file.flush()
        except Exception as e:
            print(f"Logger error: {e}")
    
    def get_log_path(self) -> str:
        return str(self.log_file)
    
    def get_public_url(self, base_url: str) -> str:
        """Convert local path to public URL."""
        filename = self.log_file.name
        base = base_url.rstrip('/')
        return f"{base}/{filename}"


async def create_logger(base_url: str = None, run_name: str = None) -> JSONLLogger:
    """Factory for creating and entering a logger."""
    logger = JSONLLogger(run_name=run_name)
    await logger.__aenter__()
    return logger