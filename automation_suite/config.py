from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class ProxySource:
    name: str
    url: str
    enabled: bool = True

@dataclass
class TargetPolicy:
    allow_external: bool = False
    allowed_domains: List[str] = field(default_factory=list)
    note: str = (
        "Targets must be explicitly authorized. Add your own domains/apps to allowed_domains."
    )

@dataclass
class SuiteConfig:
    name: str = "AutomationSuite"
    enabled_modules: List[str] = field(
        default_factory=lambda: ["browser", "proxies", "fuzzer"]
    )
    proxy_sources: List[ProxySource] = field(
        default_factory=lambda: [
            ProxySource(
                name="free-proxy-list",
                url="https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            )
        ]
    )
    target_policy: TargetPolicy = field(default_factory=TargetPolicy)
    storage_path: str = "data/automation_suite"
    max_concurrency: int = 3

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "enabled_modules": self.enabled_modules,
            "proxy_sources": [s.__dict__ for s in self.proxy_sources],
            "target_policy": {
                "allow_external": self.target_policy.allow_external,
                "allowed_domains": self.target_policy.allowed_domains,
                "note": self.target_policy.note,
            },
            "storage_path": self.storage_path,
            "max_concurrency": self.max_concurrency,
        }
