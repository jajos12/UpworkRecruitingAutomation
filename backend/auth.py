import os
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class AuthManager:
    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL")
        self.key = os.environ.get("SUPABASE_KEY")  # ANON KEY is fine for client-side, but specific logic might need Service Key
        
        if not self.url or not self.key:
            # Fallback for local dev/mock without auth
            self.client = None
            print("Warning: SUPABASE_URL or SUPABASE_KEY not set. Auth will be disabled/mocked.")
        else:
            self.client: Client = create_client(self.url, self.key)

    def login(self, email, password):
        if not self.client:
            # Mock login for development if no keys
            if email == "admin@example.com" and password == "admin":
                 return {"access_token": "mock_token", "user": {"email": email}}
            raise HTTPException(status_code=400, detail="Auth not configured")

        try:
            # Supabase GoTrue Sign In
            res = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return {
                "access_token": res.session.access_token,
                "refresh_token": res.session.refresh_token,
                "user": {
                    "id": res.user.id,
                    "email": res.user.email
                }
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def signup(self, email, password):
        if not self.client:
            raise HTTPException(status_code=400, detail="Auth not configured")
        
        try:
            res = self.client.auth.sign_up({
                "email": email,
                "password": password
            })
            # Verify if auto-confirm is on, otherwise might need to check email
            if res.user and res.session:
                 return {
                    "access_token": res.session.access_token,
                    "refresh_token": res.session.refresh_token,
                    "user": {
                        "id": res.user.id,
                        "email": res.user.email
                    }
                }
            elif res.user:
                 return {"message": "Signup successful. Please check your email for confirmation."}
            else:
                 raise Exception("Signup failed")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def verify_token(self, token: str):
        if not self.client:
            if token == "mock_token":
                return {"email": "admin@example.com"}
            raise HTTPException(status_code=401, detail="Invalid mock token")

        try:
            # Get User verify the token with Supabase
            res = self.client.auth.get_user(token)
            return res.user
        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")


# Singleton instance
auth_manager = AuthManager()
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    FastAPI dependency to protect routes.
    """
    token = credentials.credentials
    return auth_manager.verify_token(token)
