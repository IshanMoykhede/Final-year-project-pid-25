from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.supabase import connectSupa
from app.core.logging import setup_logging
from app.router.auth import router as auth_router
from app.router.file_upload import router as file_upload_router
from app.router.chat import router as chat_router
from app.router.analyzer import router as analyzer_router

# Initialize central logging configuration once
setup_logging()

app = FastAPI(title="Legal-do-ai API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(file_upload_router)
app.include_router(chat_router)
app.include_router(analyzer_router)

@app.get('/')
def boot_server():
    supabase_client = connectSupa() ; 
    return {
        "success": True,
        "msg": "Welcome to legal-do-ai Server!",
        "supabase_connected": supabase_client is not None
    }