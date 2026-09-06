from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from uuid import uuid4

from app.core.supabase import connectSupa
from app.dependencies.auth import get_current_user


router = APIRouter(
    prefix="/file-upload",
    tags=["File upload"]
)

supabase = connectSupa()

BUCKET_NAME = "Files"

ALLOWED_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
]


# -----------------------------------
# UPLOAD FILE
# -----------------------------------

@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "Only PDF and DOCX files are allowed"
            }
        )

    try:
        user_id = str(current_user["id"])
        file_id = str(uuid4())

        extension = file.filename.split(".")[-1]
        storage_path = f"{user_id}/{file_id}.{extension}"

        # Upload file to Storage
        file_data = await file.read()

        supabase.storage.from_(BUCKET_NAME).upload(
            path=storage_path,
            file=file_data,
            file_options={
                "content-type": file.content_type
            }
        )

        # Save file details in database
        supabase.table("files").insert({
            "id": file_id,
            "user_id": user_id,
            "file_name": file.filename,
            "storage_path": storage_path,
            "content_type": file.content_type,
            "status": "uploaded"
        }).execute()

        return {
            "success": True,
            "message": "File uploaded successfully",
            "data": {
                "file_id": file_id,
                "file_name": file.filename
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": str(e)
            }
        )


# -----------------------------------
# GET PREVIEW URL
# -----------------------------------

@router.get("/preview/{file_id}")
async def preview_file(
    file_id: str,
    current_user=Depends(get_current_user)
):

    try:
        # Get file details
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

        # Check ownership
        if file["user_id"] != str(current_user["id"]):
            raise HTTPException(
                status_code=403,
                detail={
                    "success": False,
                    "message": "You cannot access this file"
                }
            )

        # Generate temporary URL
        url = supabase.storage.from_(BUCKET_NAME).create_signed_url(
            file["storage_path"],
            60
        )

        return {
            "success": True,
            "message": "Preview URL created",
            "data": url
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": str(e)
            }
        )


# -----------------------------------
# GET MY FILES
# -----------------------------------

@router.get("/my-files")
async def get_my_files(
    current_user=Depends(get_current_user)
):

    try:
        result = (
            supabase
            .table("files")
            .select("*")
            .eq("user_id", str(current_user["id"]))
            .execute()
        )

        return {
            "success": True,
            "message": "Files fetched successfully",
            "data": result.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": str(e)
            }
        )


# -----------------------------------
# DELETE FILE
# -----------------------------------

@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user=Depends(get_current_user)
):

    try:
        # Find the file
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

        # Check ownership
        if file["user_id"] != str(current_user["id"]):
            raise HTTPException(
                status_code=403,
                detail={
                    "success": False,
                    "message": "You cannot delete this file"
                }
            )

        # Delete from Storage
        supabase.storage.from_(BUCKET_NAME).remove(
            [file["storage_path"]]
        )

        # Delete from database
        (
            supabase
            .table("files")
            .delete()
            .eq("id", file_id)
            .execute()
        )

        return {
            "success": True,
            "message": "File deleted successfully"
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": str(e)
            }
        )

# -----------------------------------
# TEMP TESTING ROUTE
# -----------------------------------
from app.services.ocr_service import process_document

@router.get("/test-ocr/{file_id}")
async def test_ocr_route(
    file_id: str,
    current_user=Depends(get_current_user)
):
    """
    TEMPORARY ROUTE: Used to test LlamaParse output directly in the browser.
    """
    try:
        # Note: In a real app we'd verify ownership here too!
        result = process_document(file_id)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": str(e)
            }
        )