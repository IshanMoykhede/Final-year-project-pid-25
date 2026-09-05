from fastapi import Request, Depends, HTTPException, status
from app.core.supabase import connectSupa

def get_current_user(request: Request):
    """
    Dependency to extract the JWT token from cookies,
    verify it with Supabase Auth, and return the user profile.
    """
    # Look for the token in cookies (assuming you named the cookie 'access_token')
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Missing access_token cookie."
        )
        
    supabase = connectSupa()
    
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )
    
    try:
        # 1. Verify token and get the user from Supabase Auth
        auth_response = supabase.auth.get_user(token)
        auth_user = auth_response.user
        
        if not auth_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # 2. Fetch the user's profile from the 'profiles' table
        profile_response = supabase.table("profiles").select("*").eq("id", auth_user.id).single().execute()
        profile_data = profile_response.data
        
        if not profile_data:
            # If for some reason they are in Auth but not in profiles table
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found in database"
            )
            
        return profile_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Not authenticated: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
