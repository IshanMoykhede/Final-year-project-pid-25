from fastapi import APIRouter, HTTPException, Response
from app.schemas.auth import RegisterRequest, LoginRequest
from app.core.supabase import connectSupa

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# Connect to Supabase
supabase = connectSupa()

@router.post("/register")
def register(data: RegisterRequest):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    try:
        # 1. Create the user in auth.users
        result = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password
        })

        if not result.user:
            raise HTTPException(status_code=400, detail="Unable to create user")

        # 2. Insert the username into public.profiles table
        supabase.table('profiles').insert({
            "id": result.user.id,
            "username": data.username
        }).execute()

        return {"success" : True  , "message": "Registration successful"}

    except Exception as e:
        raise HTTPException(status_code=400, detail={
            "success" : True  , 
            "message":f"Registration failed: {str(e)}"}
            )


@router.post("/login")
def login(data: LoginRequest, response: Response):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    try:
        # Authenticate the user
        result = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })

        if not result.session:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Store JWT in HttpOnly cookie
        response.set_cookie(
            key="access_token",
            value=result.session.access_token,
            httponly=True,
            secure=False, # Make sure to set this to True in production (HTTPS)
            samesite="lax"
        )

        return {"message": "Login successful"}

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid email or password: {str(e)}")
