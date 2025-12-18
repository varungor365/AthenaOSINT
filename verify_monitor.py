import sys
import logging
from modules.headless_monitor import SafeHeadlessMonitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyMonitor")

def test_monitor():
    logger.info("Starting Monitor Test...")
    try:
        monitor = SafeHeadlessMonitor(headless=True)
        
        # Test 1: Check Example Domain
        url = "https://example.com"
        keywords = ["domain", "illustrative"]
        
        logger.info(f"Checking {url}...")
        result = monitor.check_url(url, keywords)
        
        if result['status'] == 'success':
            logger.info("Test 1 Passed: Successfully visited URL.")
            if "domain" in result['matches']:
                 logger.info("Test 1 Passed: Keyword found.")
            else:
                 logger.warning("Test 1 Warning: Keyword not found (unexpected for example.com).")
        else:
            logger.error(f"Test 1 Failed: {result.get('error')}")
            
        monitor.close()
        logger.info("Monitor Test Complete.")
        
    except Exception as e:
        logger.error(f"Test Crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_monitor()
