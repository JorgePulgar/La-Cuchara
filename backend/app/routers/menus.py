"""
backend/app/routers/menus.py
Menu endpoints for persisting corrected analyzed menus.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.models.schemas import SaveMenuRequest, SaveMenuResponse
from app.services.menu_service import save_corrected_menu

router = APIRouter()


@router.post("", response_model=SaveMenuResponse, status_code=status.HTTP_201_CREATED)
async def create_menu(
	request: SaveMenuRequest,
	current_user: dict = Depends(get_current_user),
):
	"""
	Persists a corrected menu and its corrected menu items.

	The target restaurant is derived from the authenticated owner/admin user.
	"""
	if current_user.get("role") not in {"owner", "admin"}:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Only owners and admins can save menus",
		)

	try:
		menu_data, menu_items_data = await save_corrected_menu(
			current_user=current_user,
			menu_date=request.date,
			season_tag=request.season_tag,
			fields=request.fields,
			items=request.items,
		)
		return {
			"menu": menu_data,
			"menu_items": menu_items_data,
		}
	except ValueError as exc:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=str(exc),
		) from exc
	except RuntimeError as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=str(exc),
		) from exc
