import requests
import json
from typing import Dict, Any, List, Optional
from loguru import logger

class OpenBulletClient:
    """
    Client for interacting with OpenBullet2 API.
    Assumes OpenBullet2 is running locally or accessible via network.
    """
    
    def __init__(self, base_url: str = "http://localhost:8069", api_password: str = "admin"):
        self.base_url = base_url.rstrip('/')
        self.api_password = api_password # OB2 usually uses a password or API key setup
        # Note: OB2 default setup often requires initial UI interaction to set login.
        # We will assume a configured instance or default 'admin'/'admin' for now.
        self.token = None
        self.headers = {
            'Content-Type': 'application/json'
        }

    def login(self, username: str = "admin", password: str = "admin") -> bool:
        """
        Authenticate with OpenBullet2.
        """
        try:
            endpoint = f"{self.base_url}/api/v1/auth/login"
            payload = {
                "username": username,
                "password": password
            }
            response = requests.post(endpoint, json=payload, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                self.headers['Authorization'] = f"Bearer {self.token}"
                return True
            else:
                logger.error(f"OpenBullet Login Failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"OpenBullet Connection Error: {e}")
            return False

    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all jobs."""
        if not self.token: self.login()
        try:
            response = requests.get(f"{self.base_url}/api/v1/job", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Error listing jobs: {e}")
            return []

    def create_job(self, config_id: str, wordlist_id: str, bots: int = 1) -> bool:
        """Create a new MultiRunJob."""
        if not self.token: self.login()
        payload = {
            "type": "MultiRunJob",
            "configId": config_id,
            "wordlistId": wordlist_id,
            "bots": bots
        }
        try:
            response = requests.post(f"{self.base_url}/api/v1/job", json=payload, headers=self.headers)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            return False

    def start_job(self, job_id: int) -> bool:
        if not self.token: self.login()
        try:
            response = requests.post(f"{self.base_url}/api/v1/job/{job_id}/start", headers=self.headers)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error starting job: {e}")
            return False

    def get_system_status(self) -> Dict[str, Any]:
        """Get CPU/Ram usage of OB2."""
        # This endpoint is hypothetical/common, might vary in actual OB2
        if not self.token: self.login()
        try:
            response = requests.get(f"{self.base_url}/api/v1/info", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception:
            return {}
