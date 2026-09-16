from fastapi import Request, HTTPException, Depends
from app.core.supabase import connectSupa


def get_current_user(request: Request):
    # 1. Try Authorization header (Bearer token)
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()

    # 2. Fallback to access_token cookie
    if not token:
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


def verify_file_ownership(file_id: str, current_user=Depends(get_current_user)) -> dict:
    """
    Centralized security dependency:
    Verifies that the requested file exists and belongs to the authenticated user.
    Prevents IDOR (Insecure Direct Object Reference) vulnerabilities across all routes.
    """
    supabase = connectSupa()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection failed")

    result = (
        supabase
        .table("files")
        .select("*")
        .eq("id", file_id)
        .maybe_single()
        .execute()
    )

    file = result.data if result else None

    if not file:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": "File not found"
            }
        )

    if file.get("user_id") != str(current_user["id"]):
        raise HTTPException(
            status_code=403,
            detail={
                "success": False,
                "message": "Access denied: You do not own this document"
            }
        )

    return file