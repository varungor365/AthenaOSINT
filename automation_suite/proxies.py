from typing import List, Tuple
import requests

DEFAULT_TIMEOUT = 5

class ProxyManager:
    def __init__(self, sources: List[dict]):
        self.sources = [s for s in sources if s.get("enabled", True)]
        self._proxies: List[str] = []

    def fetch(self) -> List[str]:
        proxies: List[str] = []
        for src in self.sources:
            url = src.get("url")
            try:
                r = requests.get(url, timeout=DEFAULT_TIMEOUT)
                if r.ok:
                    for line in r.text.splitlines():
                        line = line.strip()
                        if ":" in line:
                            proxies.append(line)
            except Exception:
                # ignore fetch errors, continue
                pass
        # de-duplicate
        self._proxies = sorted(set(proxies))
        return self._proxies

    def list(self) -> List[str]:
        return self._proxies

    def test(self, proxy: str, test_url: str = "https://httpbin.org/ip") -> Tuple[bool, float]:
        try:
            r = requests.get(test_url, proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, timeout=DEFAULT_TIMEOUT)
            return (r.ok, r.elapsed.total_seconds())
        except Exception:
            return (False, -1.0)
