from fastapi import APIRouter, HTTPException, Request, Response
from app.schemas.auth import RegisterRequest, LoginRequest
from app.core.supabase import connectSupa

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def set_auth_cookies(response: Response, session) -> None:
    response.set_cookie(
        key=ACCESS_COOKIE,
        value=session.access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=session.refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
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

        return {"message": "Registration successful"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")


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
        set_auth_cookies(response, result.session)

        return {"message": "Login successful"}

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid email or password: {str(e)}")


@router.post("/refresh")
def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh session expired")

    try:
        result = supabase.auth.refresh_session(refresh_token)
        if not result.session:
            raise HTTPException(status_code=401, detail="Refresh session expired")

        set_auth_cookies(response, result.session)
        return {"message": "Session refreshed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unable to refresh session: {str(e)}")


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")
    return {"message": "Logout successful"}
