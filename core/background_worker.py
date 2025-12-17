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
                            value=item['value'],
                            source=item['source'],
                            context=item.get('context', ''),
                            confidence=1.0 # Self-uploaded data is high confidence
                        )
                        
                        # 2.1. SELF-LEARNING TRIGGER (Autonomous Deep Check)
                        # If we find a new Email, we recursively scan it to gather MORE data.
                        if item['type'] == 'email' and self.running:
                            logger.info(f"  [Auto-Learning] Discovered new target: {item['value']}. Queuing deep check...")
                            self._trigger_recursive_scan(item['value'])

                # 2.5 LlamaIndex Ingestion (Searchable Knowledge)
                try:
                    from intelligence.store import IntelligenceStore
                    store = IntelligenceStore()
                    store.ingest_document(str(file_path))
                except Exception as le:
                    logger.error(f"LlamaIndex Ingestion Failed: {le}")
                
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

    def _trigger_recursive_scan(self, target):
        """
        Launch a background scan on a newly discovered target.
        This fulfils the 'Self-Learning' ecosystem requirement.
        """
        try:
            # Avoid circular imports by importing within method
            from core.engine import AthenaEngine
            
            # Run in a separate thread to not block the ingestion loop
            def _scan_task():
                try:
                    logger.info(f">>> [Deep Check] Starting autonomous scan on {target}")
                    engine = AthenaEngine(target_query=target, quiet=True)
                    # We run a 'comprehensive' set of modules
                    engine.run_scan(['sherlock', 'holehe', 'leak_checker', 'smart_scraper'])
                    logger.success(f"<<< [Deep Check] Autonomous scan on {target} complete.")
                except Exception as e:
                    logger.error(f"Autonomous scan failed: {e}")

            threading.Thread(target=_scan_task, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Failed to trigger recursive scan: {e}")

    def stop(self):
        self.running = False
