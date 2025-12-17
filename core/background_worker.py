"""
Background Worker.
Runs 24/7 in the background (Daemon) to ingest data and perform analysis.
"""

import time
import threading
import os
import shutil
from pathlib import Path
from loguru import logger
from intelligence.data_ingestor import DataIngestor
from intelligence.memory_bank import MemoryBank

UPLOAD_DIR = Path("data/uploads")
PROCESSED_DIR = Path("data/processed")
FAILED_DIR = Path("data/failed")

class BackgroundWorker(threading.Thread):
    """Deep Analysis Daemon."""
    
    def __init__(self):
        super().__init__()
        self.daemon = True # Dies when main app dies
        self.ingestor = DataIngestor()
        self.memory = MemoryBank()
        self.running = True
        
        # Ensure dirs exist
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        FAILED_DIR.mkdir(parents=True, exist_ok=True)

    def run(self):
        logger.info("Background Worker (Project ARCHIVE) Started.")
        while self.running:
            try:
                self.process_queue()
            except Exception as e:
                logger.error(f"Worker Loop Error: {e}")
            
            # Low-and-slow interval (e.g. check every 30s)
            time.sleep(30)

    def process_queue(self):
        """Check upload directory for new files/databases."""
        files = list(UPLOAD_DIR.glob("*"))
        if not files:
            return

        for file_path in files:
            logger.info(f"[ARCHIVE] Ingesting file: {file_path.name}")
            try:
                # 1. Digest
                data = self.ingestor.process_file(str(file_path))
                
                # 2. Learn (Store in Memory Bank)
                if data:
                    logger.info(f"  └─ Extracted {len(data)} entities. Learning...")
                    for item in data:
                        self.memory.store_entity(
                            type=item['type'],
                            value=item['value'],
                            source=item['source'],
                            context=item.get('context', ''),
                            confidence=1.0 # Self-uploaded data is high confidence
                        )
                
                # 3. Archive (Move to processed)
                dest_path = PROCESSED_DIR / file_path.name
                shutil.move(str(file_path), str(dest_path))
                logger.success(f"  └─ File {file_path.name} processed and archived.")

                # 4. Cloud Vault Sync (Auto-Backup)
                try:
                    from core.vault import CloudVault
                    vault = CloudVault()
                    if vault.enabled:
                        vault.upload_file(str(dest_path), object_name=f"breaches/{file_path.name}")
                except Exception as ve:
                    logger.error(f"Cloud Vault Sync Failed: {ve}")
                
            except Exception as e:
                logger.error(f"  └─ Failed to process {file_path.name}: {e}")
                shutil.move(str(file_path), str(FAILED_DIR / file_path.name))

    def stop(self):
        self.running = False
