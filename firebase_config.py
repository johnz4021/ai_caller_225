import os
import json
from firebase_admin import credentials, firestore, initialize_app

class FirebaseConfig:
    def __init__(self):
        self.app = None
        self.db = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase with service account credentials from environment variable"""
        try:
            # Get credentials from environment variable
            service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
            
            if not service_account_json:
                raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON environment variable is required")
            
            # Parse JSON from environment variable
            service_account_info = json.loads(service_account_json)
            cred = credentials.Certificate(service_account_info)
            print("✅ Using Firebase credentials from environment variable")
            
            # Initialize Firebase app
            self.app = initialize_app(cred)
            self.db = firestore.client()
            print("✅ Firebase initialized successfully")
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
            raise
        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            raise
    
    def get_db(self):
        """Get Firestore database instance"""
        if self.db is None:
            raise Exception("Firebase not initialized")
        return self.db

# Global instance
firebase_config = FirebaseConfig() 