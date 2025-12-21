import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
from config import load_config
from core.engine import AthenaEngine
from modules import breach_harvester

def test_config():
    print("[*] Testing Config...")
    config = load_config()
    max_threads = config.get('MAX_CONCURRENT_MODULES')
    timeout = config.get('MODULE_TIMEOUT')
    
    print(f"Max Threads: {max_threads}")
    print(f"Timeout: {timeout}")
    
    if max_threads < 2:
        print("[!] Max Threads too low for parallel test.")
    else:
        print("[+] Config looks optimized.")

def test_engine_parallelism():
    print("\n[*] Testing Engine Parallelism...")
    engine = AthenaEngine("test_target", quiet=True)
    
    # Mock _run_module to sleep 2 seconds
    original_run = engine._run_module
    
    def mock_run(module_name):
        time.sleep(2)
        print(f"    Finished {module_name}")
        
    engine._run_module = mock_run
    
    # Run 3 modules. 
    # Sequential: 3 * 2 = 6s
    # Parallel (with >2 threads): ~2s
    
    start = time.time()
    engine.run_scan(['mod1', 'mod2', 'mod3'])
    duration = time.time() - start
    
    print(f"Scan Duration: {duration:.2f}s")
    
    if duration < 5:
        print("[+] Parallel execution confirmed (Speedup achieved).")
    else:
        print("[-] Execution seems sequential (Slow).")

def test_harvester_capabilities():
    print("\n[*] Testing Harvester Capabilities...")
    # Check if googlesearch is importable
    try:
        from googlesearch import search
        print("[+] googlesearch-python is installed.")
    except ImportError:
        print("[-] googlesearch-python MISSING.")

    # Check dork list in breach_harvester (simple grep)
    import inspect
    source = inspect.getsource(breach_harvester.scan)
    if "dorks =" in source:
        print("[+] Breach Harvester has dorking logic.")
    else:
        print("[-] Breach Harvester missing dorking logic.")

if __name__ == "__main__":
    test_config()
    test_engine_parallelism()
    test_harvester_capabilities()
