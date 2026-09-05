from fastapi import FastAPI
from app.core.supabase import connectSupa
from app.router.auth import router as auth_router

app = FastAPI(title="Legal-do-ai API")

app.include_router(auth_router)

@app.get('/')
def boot_server():
    supabase_client = connectSupa() ; 
    return {
        "success": True,
        "msg": "Welcome to legal-do-ai Server!",
        "supabase_connected": supabase_client is not None
    }