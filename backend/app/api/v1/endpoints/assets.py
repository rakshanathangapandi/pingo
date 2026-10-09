from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.database import get_db
from app.api.deps import get_current_active_user, get_current_admin
from app.models import (
    User, Asset, AssetCategory, AssetStatus,
    AssetStatusHistory
)
from app.schemas import (
    AssetCreate, AssetUpdate, AssetResponse, AssetFilter,
    AssetStatusHistoryResponse, AssetDocument, AssetExternalLink,
    PaginationParams, PaginatedResponse
)


router = APIRouter()


def generate_asset_id(db: Session) -> str:
    """Generate unique asset ID like AST-2024-001."""
    from datetime import datetime
    year = datetime.utcnow().year
    count = db.query(Asset).filter(
        Asset.asset_id.like(f"AST-{year}-%")
    ).count()
    return f"AST-{year}-{count + 1:03d}"


@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset(
    asset_in: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new asset (admin only)."""
    # Check if asset_id already exists
    existing = db.query(Asset).filter(Asset.asset_id == asset_in.asset_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Asset ID already exists")
    
    asset = Asset(
        **asset_in.model_dump(
            exclude={"assignee_id", "documents", "external_links"},
            exclude_unset=True
        ),
        assignee_id=asset_in.assignee_id,
        documents=[doc.model_dump() for doc in (asset_in.documents or [])],
        external_links=[link.model_dump() for link in (asset_in.external_links or [])],
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    
    # Create initial status history
    history = AssetStatusHistory(
        asset_id=asset.id,
        new_status=AssetStatus.AVAILABLE,
        changed_by_id=current_user.id,
        notes="Asset created"
    )
    db.add(history)
    db.commit()
    
    return asset


@router.get("/", response_model=PaginatedResponse)
def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[AssetCategory] = None,
    status: Optional[AssetStatus] = None,
    assignee_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List assets with filters and pagination."""
    query = db.query(Asset)
    
    # Non-admins only see assets assigned to them
    if current_user.role.value not in ["admin", "manager"]:
        query = query.filter(Asset.assignee_id == current_user.id)
    elif assignee_id:
        query = query.filter(Asset.assignee_id == assignee_id)
    
    if category:
        query = query.filter(Asset.category == category)
    if status:
        query = query.filter(Asset.status == status)
    if search:
        query = query.filter(
            or_(
                Asset.name.ilike(f"%{search}%"),
                Asset.asset_id.ilike(f"%{search}%"),
                Asset.description.ilike(f"%{search}%"),
                Asset.location.ilike(f"%{search}%"),
                Asset.vendor.ilike(f"%{search}%")
            )
        )
    
    total = query.count()
    assets = query.order_by(Asset.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        items=assets,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get asset by ID."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    if current_user.role.value not in ["admin", "manager"] and asset.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return asset


@router.patch("/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: int,
    asset_update: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update an asset (admin only)."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    update_data = asset_update.model_dump(exclude_unset=True)
    old_status = asset.status
    
    # Handle documents and external_links
    if "documents" in update_data:
        update_data["documents"] = [doc.model_dump() for doc in update_data["documents"]]
    if "external_links" in update_data:
        update_data["external_links"] = [link.model_dump() for link in update_data["external_links"]]
    
    for field, value in update_data.items():
        setattr(asset, field, value)
    
    # Handle status change
    if "status" in update_data and update_data["status"] != old_status:
        history = AssetStatusHistory(
            asset_id=asset.id,
            old_status=old_status,
            new_status=update_data["status"],
            changed_by_id=current_user.id,
        )
        db.add(history)
    
    db.commit()
    db.refresh(asset)
    return asset


@router.post("/{asset_id}/assign", response_model=AssetResponse)
def assign_asset(
    asset_id: int,
    assignee_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Assign asset to a user (admin only)."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    assignee = db.query(User).filter(User.id == assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee not found")
    
    old_status = asset.status
    asset.assignee_id = assignee_id
    asset.status = AssetStatus.ASSIGNED
    
    history = AssetStatusHistory(
        asset_id=asset.id,
        old_status=old_status,
        new_status=AssetStatus.ASSIGNED,
        changed_by_id=current_user.id,
        notes=f"Assigned to {assignee.full_name or assignee.email}" + (f": {notes}" if notes else "")
    )
    db.add(history)
    db.commit()
    db.refresh(asset)
    return asset


@router.post("/{asset_id}/return", response_model=AssetResponse)
def return_asset(
    asset_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Return asset to available (admin only)."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    old_status = asset.status
    old_assignee = asset.assignee_id
    asset.assignee_id = None
    asset.status = AssetStatus.AVAILABLE
    
    history = AssetStatusHistory(
        asset_id=asset.id,
        old_status=old_status,
        new_status=AssetStatus.AVAILABLE,
        changed_by_id=current_user.id,
        notes=f"Returned by {current_user.full_name or current_user.email}" + (f": {notes}" if notes else "")
    )
    db.add(history)
    db.commit()
    db.refresh(asset)
    return asset


@router.delete("/{asset_id}")
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete an asset (admin only)."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    db.delete(asset)
    db.commit()
    return {"message": "Asset deleted successfully"}