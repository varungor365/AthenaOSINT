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

        # Start Monitor Thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

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
                # 1. SPECIAL HANDLING: Combo Lists (Breach Vault)
                # Check if this is a combo list first using BreachProcessor
                is_combo, stats, analysis = False, {}, {}
                
                try:
                    from modules.breach_processor import BreachProcessor
                    from intelligence.breach_analyzer import BreachAnalyzer
                    
                    processor = BreachProcessor()
                    # Check first 5 lines
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        head = [next(f).strip() for _ in range(5)]
                    
                    # Heuristic: at least 3/5 lines have a separator and look like user:pass
                    valid_lines = sum(1 for line in head if processor.parse_line(line)[0] is not None)
                    
                    if valid_lines >= 3:
                        logger.info(f"  [Breach Vault] Detected combo list: {file_path.name}")
                        is_combo = True
                        
                        # A. Clean & Sort
                        clean_path = PROCESSED_DIR / f"clean_{file_path.name}"
                        stats = processor.clean_combos(file_path, clean_path)
                        
                        # B. AI Analysis
                        analyzer = BreachAnalyzer()
                        # Read sample from clean file for analysis
                        with open(clean_path, 'r', encoding='utf-8') as f:
                            sample_combos = [line.strip() for _, line in zip(range(100), f)]
                        
                        analysis = analyzer.analyze_batch(sample_combos)
                        
                        # Save Analysis Report
                        report_data = {
                            "filename": file_path.name,
                            "stats": stats,
                            "analysis": analysis,
                            "timestamp": time.time()
                        }
                        
                        report_path = Path(f"data/reports/vault_{int(time.time())}.json")
                        report_path.parent.mkdir(parents=True, exist_ok=True)
                        import json
                        with open(report_path, 'w') as f:
                            json.dump(report_data, f, indent=2)
                            
                        logger.info(f"  [Breach Vault] Analysis saved to {report_path}")
                        
                        # C. Active Mega.nz Checker (User Request)
                        # Only if enabled in config
                        from config import get_config
                        if get_config().get('ENABLE_ACTIVE_CHECKING', False):
                            logger.info(f"  [Mega Checker] Active checking enabled. Validating {len(sample_combos)} combos...")
                            from modules.mega_checker import MegaChecker
                            mega_checker = MegaChecker()
                            
                            # Check a batch (limit to 50 for safety in this demo)
                            valid_hits = mega_checker.check_batch(sample_combos[:50])
                            
                            if valid_hits:
                                logger.success(f"  [Mega Checker] Found {len(valid_hits)} VALID Mega.nz accounts!")
                                # Save hits
                                hits_path = Path(f"data/reports/mega_hits_{int(time.time())}.json")
                                with open(hits_path, 'w') as f:
                                    json.dump(valid_hits, f, indent=2)

                        # Replace original file with cleaned version for generic ingestion?
                        # Or just ingest the cleaned version.
                        # For now, we perform generic ingestion on the ORIGINAL file as before, 
                        # but we have the vault stats now.
                except Exception as e:
                     logger.warning(f"Combo detection/processing failed: {e}")

                # 2. Generic Ingestion (Entity Extraction)
                # Use stream to avoid loading entire file into memory
                entity_count = 0
                for item in self.ingestor.process_file_stream(str(file_path)):
                    entity_count += 1
                    
                    self.memory.store_entity(
                        value=item['value'],
                        source=item['source'],
                        context=item.get('context', ''),
                        confidence=1.0 # Self-uploaded data is high confidence
                    )
                    
                    # 2.1. SELF-LEARNING TRIGGER (Autonomous Deep Check)
                    # If we find a new Email, we recursively scan it to gather MORE data.
                    if item['type'] == 'email' and self.running:
                        # Throttle: Only trigger for every 50th email to avoid DDOSing self or APIs
                        if entity_count % 50 == 0:
                            logger.info(f"  [Auto-Learning] Discovered new target: {item['value']}. Queuing deep check...")
                            self._trigger_recursive_scan(item['value'])

                logger.info(f"  └─ Extracted {entity_count} entities from {file_path.name}.")

                # 2.5 LlamaIndex Ingestion (Searchable Knowledge)
                try:
                    from intelligence.store import IntelligenceStore
                    store = IntelligenceStore()
                    store.ingest_document(str(file_path))
                except Exception as le:
                    logger.warning(f"LlamaIndex Ingestion Failed (Non-fatal): {le}")
                
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
                # Ensure we don't loop forever on failed file
                target_failed = FAILED_DIR / file_path.name
                if target_failed.exists():
                     timestamp = int(time.time())
                     target_failed = FAILED_DIR / f"{file_path.name}_{timestamp}"
                
                try:
                    shutil.move(str(file_path), str(target_failed))
                except Exception as mv_err:
                    logger.error(f"Failed to move to failed dir: {mv_err}")

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

    def _monitor_loop(self):
        """
        Secondary thread for Safe Headless Monitoring.
        Checks user-defined public URLs periodically.
        """
        from modules.headless_monitor import SafeHeadlessMonitor
        import json
        
        logger.info("[MONITOR] Initializing Safe Headless Monitor...")
        monitor = SafeHeadlessMonitor(headless=True)
        
        # Default targets if config doesn't exist
        default_targets = [
            {"url": "https://stackoverflow.com/questions/tagged/security", "keywords": ["vulnerability", "cvss"]},
            {"url": "https://github.com/trending", "keywords": ["leak", "database"]}
        ]
        
        targets_file = Path("data/monitor_targets.json")
        
        while self.running:
            try:
                # Load targets dynamically so user can update file
                targets = []
                if targets_file.exists():
                    try:
                        with open(targets_file, 'r') as f:
                            targets = json.load(f)
                    except Exception as e:
                        logger.error(f"[MONITOR] Failed to load targets: {e}")
                
                if not targets:
                    targets = default_targets
                    # Create default file if missing (and not ignored/blocked by permissions)
                    if not targets_file.exists():
                        try:
                            with open(targets_file, 'w') as f:
                                json.dump(default_targets, f, indent=2)
                        except:
                            pass

                logger.info("[MONITOR] Starting check cycle...")
                for target in targets:
                    if not self.running: break
                    
                    url = target.get('url')
                    keywords = target.get('keywords', [])
                    
                    if url:
                        # logger.info(f"[MONITOR] Checking {url}...")
                        monitor.check_url(url, keywords)
                        # Be kind to the web
                        time.sleep(10)
                
                # Sleep for 1 hour approx (3600s) but check self.running often
                for _ in range(60): 
                    if not self.running: break
                    time.sleep(60)
                    
            except Exception as e:
                logger.error(f"[MONITOR] Loop Error: {e}")
                time.sleep(60)

        monitor.close()
        logger.info("[MONITOR] Stopped.")
