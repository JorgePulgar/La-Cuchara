"""
backend/app/routers/images.py
Endpoints for image processing and analysis using Azure Content Understanding.
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Query

from app.services.image_analysis_service import (
    analyze_menu_image,
    extract_structured_fields,
    ImageAnalysisConfigError,
    ImageAnalysisError,
    OperationTimeoutError,
)
from app.models.schemas import ImageAnalysisResponse, ExtractedField, BoundingRegion

router = APIRouter()
logger = logging.getLogger(__name__)

# Constants
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/bmp",
    "image/gif",
    "image/tiff",
}


@router.post("/analyze-menu", response_model=ImageAnalysisResponse)
async def analyze_menu(
    file: UploadFile = File(
        ...,
        description="Menu image file (JPEG, PNG, WebP, BMP, GIF, TIFF)"
    ),
    restaurant_id: str | None = Query(
        None,
        description="Optional restaurant ID to associate the analysis with"
    ),
):
    """
    Analyzes a menu image using Azure Content Understanding.

    Process:
    1. Validates image file (size, format)
    2. Reads binary image data
    3. Sends to Azure Content Understanding API via analyzeBinary
    4. Polls operation until completion (max 30 attempts, 1.5s interval)
    5. Returns extracted fields and structured data

    Args:
        file: Upload image file (required)
        restaurant_id: Optional UUID string to associate with the analysis

    Returns:
        ImageAnalysisResponse with extracted fields and structured items

    Raises:
        HTTPException 400: Invalid image format or size
        HTTPException 500: Configuration error or image analysis failure
        HTTPException 502: Azure API error or timeout
    """

    # =========================================================================
    # Step 1: Validate file type
    # =========================================================================
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        msg = (
            f"Invalid image format: {file.content_type}. "
            f"Allowed formats: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}"
        )
        logger.warning(f"[{restaurant_id}] {msg}")
        raise HTTPException(status_code=400, detail=msg)

    # =========================================================================
    # Step 2: Read and validate file size
    # =========================================================================
    try:
        image_bytes = await file.read()

        if len(image_bytes) == 0:
            msg = "Image file is empty"
            logger.warning(f"[{restaurant_id}] {msg}")
            raise HTTPException(status_code=400, detail=msg)

        if len(image_bytes) > MAX_IMAGE_SIZE:
            size_mb = MAX_IMAGE_SIZE / (1024 * 1024)
            msg = f"Image file too large. Maximum size: {size_mb}MB, actual size: {len(image_bytes) / (1024 * 1024):.2f}MB"
            logger.warning(f"[{restaurant_id}] {msg}")
            raise HTTPException(status_code=413, detail=msg)

        logger.info(f"[{restaurant_id}] Image file validated. Size: {len(image_bytes)} bytes")

    except HTTPException:
        raise
    except Exception as e:
        msg = f"Error reading image file: {str(e)}"
        logger.error(f"[{restaurant_id}] {msg}")
        raise HTTPException(status_code=400, detail=msg)

    # =========================================================================
    # Step 3: Send to Azure Content Understanding API
    # =========================================================================
    try:
        logger.info(f"[{restaurant_id}] Starting Azure Content Understanding analysis")

        # Call the Azure service
        analysis_result = await analyze_menu_image(image_bytes)

        logger.info(f"[{restaurant_id}] Azure analysis completed successfully")

        # =====================================================================
        # Step 4: Extract and structure fields
        # =====================================================================
        raw_fields = analysis_result.get("fields", {})
        raw_result = analysis_result.get("raw_result", {})

        # Build structured items list
        items = []
        for field_name, field_value in raw_fields.items():
            if isinstance(field_value, dict):
                bounding_regions = [
                    BoundingRegion(
                        page_number=br.get("pageNumber"),
                        polygon=br.get("polygon"),
                    )
                    for br in field_value.get("boundingRegions", [])
                ]

                items.append(
                    ExtractedField(
                        name=field_name,
                        content=field_value.get("content", ""),
                        confidence=float(field_value.get("confidence", 0.0)),
                        bounding_regions=bounding_regions,
                    )
                )
            else:
                items.append(
                    ExtractedField(
                        name=field_name,
                        content=str(field_value),
                        confidence=1.0,
                        bounding_regions=[],
                    )
                )

        # Return structured response
        response = ImageAnalysisResponse(
            status="succeeded",
            fields=raw_fields,
            items=items,
        )

        logger.debug(f"[{restaurant_id}] Extracted {len(items)} fields from image")
        return response

    # =========================================================================
    # Step 5: Handle specific error types with appropriate HTTP status codes
    # =========================================================================
    except ImageAnalysisConfigError as e:
        msg = f"Azure configuration error: {str(e)}"
        logger.error(f"[{restaurant_id}] {msg}")
        raise HTTPException(status_code=500, detail=msg)

    except OperationTimeoutError as e:
        msg = f"Image analysis timed out: {str(e)}"
        logger.error(f"[{restaurant_id}] {msg}")
        raise HTTPException(status_code=504, detail=msg)

    except ImageAnalysisError as e:
        msg = f"Azure image analysis failed: {str(e)}"
        logger.error(f"[{restaurant_id}] {msg}")
        raise HTTPException(status_code=502, detail=msg)

    except HTTPException:
        raise

    except Exception as e:
        msg = f"Unexpected error during image analysis: {str(e)}"
        logger.error(f"[{restaurant_id}] {msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=msg)


@router.get("/health")
async def health_check():
    """
    Health check endpoint for image analysis service.

    Returns:
        dict with service status and provider information
    """
    return {
        "status": "ok",
        "service": "image-analysis",
        "provider": "azure-content-understanding",
        "api_version": "2025-11-01",
    }

