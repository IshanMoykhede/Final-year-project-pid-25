from fastapi import Request, HTTPException
from app.core.supabase import connectSupa


def get_current_user(request: Request):

    # Get token from cookie
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "message": "Authentication token not found"
            }
        )

    supabase = connectSupa()

    if not supabase:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to connect to Supabase"
            }
        )

    try:
        # Verify token and get authenticated user
        user = supabase.auth.get_user(token).user

        if not user:
            raise HTTPException(
                status_code=401,
                detail={
                    "success": False,
                    "message": "Invalid or expired token"
                }
            )

        # Get user's profile
        profile = (
            supabase
            .table("profiles")
            .select("*")
            .eq("id", user.id)
            .single()
            .execute()
        )

        if not profile.data:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "message": "User profile not found"
                }
            )

        # Return current user's profile
        return profile.data

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "message": f"Authentication failed: {str(e)}"
            }
        )