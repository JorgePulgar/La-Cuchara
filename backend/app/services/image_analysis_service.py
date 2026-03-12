"""
backend/app/services/image_analysis_service.py
Service for analyzing menu images using Azure Content Understanding REST API.

Handles:
- Base64 encoding of binary image data
- Async HTTP requests to Azure Content Understanding
- Long-running operation polling with exponential backoff
- Structured error handling and logging
"""

import base64
import asyncio
import logging
from typing import Any
import httpx

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AzureContentUnderstandingError(Exception):
    """Base exception for Azure Content Understanding errors."""
    pass


class ImageAnalysisConfigError(AzureContentUnderstandingError):
    """Raised when Azure credentials are not properly configured."""
    pass


class ImageAnalysisError(AzureContentUnderstandingError):
    """Raised when image analysis fails."""
    pass


class OperationTimeoutError(AzureContentUnderstandingError):
    """Raised when polling operation exceeds max retries."""
    pass


async def validate_configuration() -> None:
    """
    Validates that all required Azure Content Understanding configuration is present.

    Raises:
        ImageAnalysisConfigError: If any required configuration is missing.
    """
    missing_vars = []

    if not settings.AZURE_CU_ENDPOINT:
        missing_vars.append("AZURE_CU_ENDPOINT")
    if not settings.AZURE_CU_KEY:
        missing_vars.append("AZURE_CU_KEY")
    if not settings.AZURE_CU_ANALYZER_ID:
        missing_vars.append("AZURE_CU_ANALYZER_ID")

    if missing_vars:
        error_msg = f"Missing Azure Content Understanding configuration: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ImageAnalysisConfigError(error_msg)


async def analyze_menu_image(image_bytes: bytes) -> dict[str, Any]:
    """
    Analyzes a menu image using Azure Content Understanding REST API.

    Process:
    1. Validates configuration
    2. Encodes image to base64
    3. Sends analyzeBinary request (returns 202 Accepted)
    4. Polls operation status every 1.5 seconds
    5. Returns extracted fields when status is "Succeeded"

    Args:
        image_bytes: Binary image data (PNG, JPEG, etc.)

    Returns:
        Dictionary containing extracted fields from the analyzed image.

    Raises:
        ImageAnalysisConfigError: If Azure credentials are not configured.
        ImageAnalysisError: If the API request fails or returns an error.
        OperationTimeoutError: If polling exceeds 30 attempts without completion.
    """
    # Validate configuration first
    await validate_configuration()

    # logger.info(f"Starting image analysis. Image size: {len(image_bytes)} bytes")
    print(f"Starting image analysis. Image size: {len(image_bytes)} bytes")

    # Step 1: Encode image to base64
    try:
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        logger.debug(f"Image encoded to base64. Encoded size: {len(image_base64)} bytes")
    except Exception as e:
        error_msg = f"Failed to encode image to base64: {str(e)}"
        logger.error(error_msg)
        raise ImageAnalysisError(error_msg)

    # Step 2: Build the analyzeBinary request URL
    endpoint = settings.AZURE_CU_ENDPOINT.rstrip("/")
    analyzer_id = settings.AZURE_CU_ANALYZER_ID
    api_version = "2025-11-01"

    analyze_url = (
        f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}:analyzeBinary"
        f"?api-version={api_version}"
    )

    headers = {
        "Ocp-Apim-Subscription-Key": settings.AZURE_CU_KEY,
        "Content-Type": "application/octet-stream",
    }

    # logger.info(f"Sending analyzeBinary request to: {analyze_url}")
    print(f"Sending analyzeBinary request to: {analyze_url}")

    # Step 3: Send the initial request and handle 202 Accepted
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                analyze_url,
                content=image_bytes,
                headers=headers,
            )

            logger.debug(f"Initial response status: {response.status_code}")

            if response.status_code != 202:
                error_body = response.text
                error_msg = (
                    f"Azure API returned unexpected status {response.status_code}. "
                    f"Expected 202 Accepted. Response: {error_body}"
                )
                logger.error(error_msg)
                raise ImageAnalysisError(error_msg)

            # Extract Operation-Location from headers
            operation_location = response.headers.get("Operation-Location")
            if not operation_location:
                error_msg = "Operation-Location header not found in 202 response"
                logger.error(error_msg)
                raise ImageAnalysisError(error_msg)

            # logger.info(f"Operation created. Polling URL: {operation_location}")
            print(f"Operation created. Polling URL: {operation_location}")

        except httpx.RequestError as e:
            error_msg = f"Network error during analyzeBinary request: {str(e)}"
            logger.error(error_msg)
            raise ImageAnalysisError(error_msg)
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error during analyzeBinary request: {str(e)}"
            logger.error(error_msg)
            raise ImageAnalysisError(error_msg)

    # Step 4: Poll the operation until completion
    max_retries = 30
    retry_delay = 1.5  # seconds
    attempt = 0

    while attempt < max_retries:
        attempt += 1
        logger.debug(f"Polling attempt {attempt}/{max_retries}")

        await asyncio.sleep(retry_delay)

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                poll_response = await client.get(
                    operation_location,
                    headers={
                        "Ocp-Apim-Subscription-Key": settings.AZURE_CU_KEY,
                    },
                )

                if poll_response.status_code != 200:
                    error_msg = (
                        f"Polling returned unexpected status {poll_response.status_code}. "
                        f"Response: {poll_response.text}"
                    )
                    logger.error(error_msg)
                    raise ImageAnalysisError(error_msg)

                result_data = poll_response.json()
                status = result_data.get("status")

                logger.debug(f"Operation status: {status}")

                if status == "Succeeded":
                    logger.info("Operation completed successfully")
                    logger.debug(f"Result data: {result_data}")
                    print(f"Result data: {result_data}")

                    # Extract fields from the result
                    try:
                        extracted_fields = result_data.get("result", {}).get("contents", [{}])[0].get("fields", {})
                        logger.info(f"Extracted {len(extracted_fields)} fields from image")
                        return {
                            "status": "succeeded",
                            "fields": extracted_fields,
                            "raw_result": result_data,
                        }
                    except (KeyError, IndexError, TypeError) as e:
                        error_msg = f"Failed to extract fields from result: {str(e)}"
                        logger.error(error_msg)
                        raise ImageAnalysisError(error_msg)

                elif status == "Failed":
                    error_msg = f"Operation failed. Error details: {result_data.get('error', {})}"
                    logger.error(error_msg)
                    raise ImageAnalysisError(error_msg)

                # status == "NotStarted" or "Running" — continue polling
                logger.debug(f"Operation still running. Status: {status}")

            except httpx.RequestError as e:
                error_msg = f"Network error during polling (attempt {attempt}): {str(e)}"
                logger.error(error_msg)
                if attempt == max_retries:
                    raise ImageAnalysisError(error_msg)
                continue
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP error during polling (attempt {attempt}): {str(e)}"
                logger.error(error_msg)
                if attempt == max_retries:
                    raise ImageAnalysisError(error_msg)
                continue

    # Timeout occurred
    error_msg = (
        f"Operation polling timed out after {max_retries} attempts "
        f"({max_retries * retry_delay} seconds)"
    )
    logger.error(error_msg)
    raise OperationTimeoutError(error_msg)


def extract_structured_fields(raw_result: dict[str, Any]) -> dict[str, Any]:
    """
    Extracts and structures the fields from Azure Content Understanding response.

    Args:
        raw_result: Raw response from Azure Content Understanding API.

    Returns:
        Dictionary with extracted fields organized by type.
    """
    try:
        contents = raw_result.get("result", {}).get("contents", [])
        if not contents:
            return {"items": []}

        fields = contents[0].get("fields", {})

        # Organize fields by type if needed
        structured = {
            "items": [],
            "raw_fields": fields,
        }

        # Parse fields based on their structure
        for field_name, field_value in fields.items():
            if isinstance(field_value, dict):
                structured["items"].append({
                    "name": field_name,
                    "content": field_value.get("content", ""),
                    "confidence": field_value.get("confidence", 0),
                    "bounding_regions": field_value.get("boundingRegions", []),
                })
            else:
                structured["items"].append({
                    "name": field_name,
                    "content": field_value,
                    "confidence": 1.0,
                })

        return structured

    except (KeyError, IndexError, TypeError) as e:
        logger.warning(f"Error extracting structured fields: {str(e)}")
        return {"items": [], "raw_fields": raw_result}
