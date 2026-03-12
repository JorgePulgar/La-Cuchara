"""
backend/app/models/schemas.py
Pydantic v2 schemas — source of truth for all API contracts.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# =============================================================================
# Auth
# =============================================================================

class LoginRequest(BaseModel):
    """POST /auth/login request body."""
    email: EmailStr
    password: str = Field(..., min_length=6)


class SignupRequest(BaseModel):
    """POST /auth/signup request body."""
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field(default="user", pattern=r"^(user|owner)$")
    restaurant_name: str | None = Field(
        default=None,
        description="Required when role is 'owner'",
    )
    restaurant_address: str | None = Field(
        default=None,
        description="Required when role is 'owner'",
    )
    restaurant_phone: str | None = Field(
        default=None,
        description="Required when role is 'owner'",
    )


class TokenResponse(BaseModel):
    """Response returned after successful login or signup."""
    access_token: str
    refresh_token: str
    user_id: UUID
    email: str
    role: str


class RefreshTokenRequest(BaseModel):
    """Request body for refreshing a Supabase auth session."""
    refresh_token: str = Field(..., min_length=1)


# =============================================================================
# Users
# =============================================================================

class UserCreate(BaseModel):
    """Schema for creating a user in the users table."""
    id: UUID
    email: EmailStr
    role: str = Field(default="user", pattern=r"^(admin|owner|user)$")
    restaurant_id: UUID | None = None


class UserOut(BaseModel):
    """Schema for returning user data."""
    id: UUID
    email: str
    role: str
    restaurant_id: UUID | None = None


# =============================================================================
# Restaurants
# =============================================================================

class RestaurantCreate(BaseModel):
    """Schema for creating a restaurant."""
    name: str = Field(..., min_length=1)
    address: str | None = None
    lat: float | None = None
    lon: float | None = None
    phone: str | None = None
    owner_user_id: UUID | None = None


class RestaurantOut(BaseModel):
    """Schema for returning restaurant data."""
    id: UUID
    name: str
    address: str | None = None
    lat: float | None = None
    lon: float | None = None
    phone: str | None = None
    owner_user_id: UUID | None = None


# =============================================================================
# Menus
# =============================================================================

class MenuCreate(BaseModel):
    """Schema for creating a menu."""
    restaurant_id: UUID
    date: date
    source_image_id: UUID | None = None
    raw_text: str | None = None
    parsed_json: dict | None = None
    season_tag: str | None = None


class MenuOut(BaseModel):
    """Schema for returning menu data."""
    id: UUID
    restaurant_id: UUID
    date: date
    source_image_id: UUID | None = None
    raw_text: str | None = None
    parsed_json: dict | None = None
    season_tag: str | None = None


class SaveMenuRequest(BaseModel):
    """Schema for saving a corrected analyzed menu."""
    date: date
    season_tag: str | None = None
    fields: dict[str, Any] = Field(default_factory=dict)
    items: list[str] = Field(default_factory=list)


class SaveMenuResponse(BaseModel):
    """Schema returned after persisting a menu and its items."""
    menu: MenuOut
    menu_items: list["MenuItemOut"]


# =============================================================================
# Menu Items
# =============================================================================

class MenuItemCreate(BaseModel):
    """Schema for creating a menu item."""
    menu_id: UUID
    name: str = Field(..., min_length=1)
    description: str | None = None
    price: float | None = None
    tags: list | None = None
    predicted: bool = False


class MenuItemOut(BaseModel):
    """Schema for returning menu item data."""
    id: UUID
    menu_id: UUID
    name: str
    description: str | None = None
    price: float | None = None
    tags: list | None = None
    predicted: bool = False


# =============================================================================
# Images
# =============================================================================

class ImageOut(BaseModel):
    """Schema for returning image data."""
    id: UUID
    restaurant_id: UUID | None = None
    url: str
    uploaded_by: UUID
    upload_ts: datetime


# =============================================================================
# Image Analysis (Azure Content Understanding)
# =============================================================================

class BoundingRegion(BaseModel):
    """Represents a bounding region in the analyzed image."""
    page_number: int | None = None
    polygon: list[dict] | None = None


class ExtractedField(BaseModel):
    """Represents a field extracted from the analyzed image."""
    name: str
    content: str
    confidence: float
    bounding_regions: list[BoundingRegion] = []


class ImageAnalysisResponse(BaseModel):
    """Response from menu image analysis using Azure Content Understanding."""
    status: str = Field(..., description="Status of the analysis (e.g., 'succeeded')")
    fields: dict[str, Any] = Field(..., description="Raw extracted fields from the image")
    items: list[ExtractedField] = Field(
        default_factory=list,
        description="Structured list of extracted items with confidence scores"
    )


class AnalysisErrorResponse(BaseModel):
    """Error response from image analysis endpoint."""
    detail: str
    error_type: str
    status_code: int


# =============================================================================
# Ratings
# =============================================================================

class RatingCreate(BaseModel):
    """Schema for creating a rating."""
    menu_item_id: UUID
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


class RatingOut(BaseModel):
    """Schema for returning rating data."""
    id: UUID
    user_id: UUID
    menu_item_id: UUID
    rating: int
    comment: str | None = None
    ts: datetime
