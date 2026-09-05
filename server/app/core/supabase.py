import os
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# Ensure env variables are loaded before accessing them
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def connectSupa() -> Client | None:
    try:
        if  not SUPABASE_URL or not SUPABASE_KEY : 
            raise ValueError("Supabase URL or Key is missing") ; 

        supabase_client : Client = create_client(SUPABASE_URL , SUPABASE_KEY) ; 

        return supabase_client ; 
    except Exception as e :
        logging.error(f"Failed to connect supabase : {e}") ; 
        return None  ; 



