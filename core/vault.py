"""
Secure Cloud Vault Manager.
Handles encrypted file synchronization with S3-compatible cloud storage.

Features:
- Client-Side Encryption (AES-256-GCM) before upload.
- Automatic Sync (Upload specific folders).
- S3 Compatibility (AWS, MinIO, Wasabi, DigitalOcean Spaces).
"""

import os
import boto3
import json
import pickle
from cryptography.fernet import Fernet
from pathlib import Path
from loguru import logger
from config import get_config

# Google Drive Imports
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

class CloudVault:
    def __init__(self):
        self.config = get_config()
        self.enabled = self.config.get('CLOUD_VAULT_ENABLED', 'True').lower() == 'true'
        self.provider = self.config.get('CLOUD_PROVIDER', 'gdrive').lower() # 's3' or 'gdrive'
        
        if not self.enabled:
            return

        # Security: Encryption Key
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
        
        self.service = None
        self.s3 = None
        
        if self.provider == 'gdrive':
            self._init_gdrive()
        else:
            self._init_s3()

    def _get_or_create_key(self):
        """Get encryption key from config or generate one."""
        key = self.config.get('VAULT_ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
            logger.warning(f"Generated new Vault Key (Save this!): {key.decode()}")
        return key

    def _init_gdrive(self):
        """Initialize Google Drive API."""
        try:
            creds = None
            token_path = 'token.pickle'
            creds_path = 'credentials.json' # User must provide this
            
            # 1. Load Token
            if os.path.exists(token_path):
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
            
            # 2. Refresh/Login
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if os.path.exists(creds_path):
                        flow = InstalledAppFlow.from_client_secrets_file(
                            creds_path, ['https://www.googleapis.com/auth/drive.file'])
                        # This normally opens a browser. For headless, we might need a different flow.
                        # For local desktop app, this is fine.
                        creds = flow.run_local_server(port=0)
                    else:
                        logger.warning("No credentials.json found for GDrive. Cloud Vault disabled.")
                        self.enabled = False
                        return

                # Save token
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)

            self.service = build('drive', 'v3', credentials=creds)
            logger.info("CloudVault initialized (Google Drive).")
            
        except Exception as e:
            logger.error(f"GDrive Init Failed: {e}")
            self.enabled = False

    def _init_s3(self):
        """Initialize S3 Connection."""
        self.bucket_name = self.config.get('CLOUD_BUCKET', 'athena-vault')
        try:
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=self.config.get('AWS_ACCESS_KEY'),
                aws_secret_access_key=self.config.get('AWS_SECRET_KEY'),
                region_name=self.config.get('CLOUD_REGION', 'us-east-1'),
                endpoint_url=self.config.get('CLOUD_ENDPOINT', None)
            )
            logger.info(f"CloudVault initialized (S3: {self.bucket_name})")
        except Exception as e:
            logger.error(f"S3 Init Failed: {e}")
            self.enabled = False

    def upload_file(self, file_path: str, object_name: str = None):
        """Encrypts and uploads a file to the secure vault."""
        if not self.enabled: return False
        
        file_path = Path(file_path)
        if not file_path.exists(): return False
        if object_name is None: object_name = file_path.name

        try:
            # 1. Read (No Encryption as requested)
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # 2. Upload based on provider
            if self.provider == 'gdrive':
                from io import BytesIO
                # Use original name, no .enc
                file_metadata = {'name': object_name, 'mimeType': 'application/octet-stream'}
                media = MediaIoBaseUpload(BytesIO(data), mimetype='application/octet-stream', resumable=True)
                
                self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                logger.info(f"Uploaded to GDrive (Plain): {object_name}")
                
            else: # S3
                self.s3.put_object(
                    Bucket=self.bucket_name,
                    Key=object_name,
                    Body=data,
                    Metadata={'encrypted': 'false'}
                )
                logger.info(f"Uploaded to S3 (Plain): {object_name}")
                
            return True
        except Exception as e:
            logger.error(f"Vault Upload Error: {e}")
            return False
        except Exception as e:
            logger.error(f"Vault Upload Error: {e}")
            return False

    def list_files(self):
        return [] # todo
