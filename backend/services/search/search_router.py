from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.database import get_db
from core.guards import require_module
from core.security import require_roles
from models.search import SavedSearch, SearchIndexEntry
from models.user import User, UserRole
from utils.tenancy import scoped_query
from utils.write_ops import apply_training_mode, audit_and_event, model_snapshot

router = APIRouter(
    prefix="/api/search",
    tags=["Search"],
    dependencies=[Depends(require_module("SEARCH"))],
)


class SearchIndexCreate(BaseModel):
    module_key: str
    record_id: str
    title: str
    body: str
    tags: list[str] = []
    classification: str = "NON_PHI"


class SearchResult(BaseModel):
    id: int
    module_key: str
    record_id: str
    title: str
    snippet: str
    tags: list[str]
    classification: str


class SavedSearchCreate(BaseModel):
    name: str
    query: str
    filters: dict = {}


class SavedSearchResponse(BaseModel):
    id: int
    name: str
    query: str
    filters: dict

    class Config:
        from_attributes = True


@router.get("")
def search(
    request: Request,
    query: str = "",
    module: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.provider, UserRole.founder)),
):
    search_query = scoped_query(db, SearchIndexEntry, user.org_id, request.state.training_mode)
    if module:
        search_query = search_query.filter(SearchIndexEntry.module_key == module)
    if query:
        search_query = search_query.filter(
            or_(
                SearchIndexEntry.title.ilike(f"%{query}%"),
                SearchIndexEntry.body.ilike(f"%{query}%"),
            )
        )
    results = search_query.order_by(SearchIndexEntry.created_at.desc()).limit(50).all()
    return [
        SearchResult(
            id=item.id,
            module_key=item.module_key,
            record_id=item.record_id,
            title=item.title,
            snippet=item.body[:140],
            tags=item.tags or [],
            classification=item.classification,
        )
        for item in results
    ]


@router.post("/index", status_code=status.HTTP_201_CREATED)
def index_record(
    payload: SearchIndexCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.provider, UserRole.founder)),
):
    entry = SearchIndexEntry(
        **payload.dict(),
        org_id=user.org_id,
    )
    apply_training_mode(entry, request)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="index",
        resource="search_index",
        classification=payload.classification,
        after_state=model_snapshot(entry),
        event_type="search.index.created",
        event_payload={"record_id": entry.record_id},
    )
    return {"status": "ok", "entry_id": entry.id}


@router.get("/saved", response_model=list[SavedSearchResponse])
def list_saved(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.provider, UserRole.founder)),
):
    return scoped_query(db, SavedSearch, user.org_id, request.state.training_mode).order_by(
        SavedSearch.created_at.desc()
    )


@router.post("/saved", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED)
def create_saved(
    payload: SavedSearchCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.provider, UserRole.founder)),
):
    saved = SavedSearch(
        org_id=user.org_id,
        name=payload.name,
        query=payload.query,
        filters=payload.filters,
        created_by=user.id,
    )
    apply_training_mode(saved, request)
    db.add(saved)
    db.commit()
    db.refresh(saved)
    audit_and_event(
        db=db,
        request=request,
        user=user,
        action="create",
        resource="saved_search",
        classification="NON_PHI",
        after_state=model_snapshot(saved),
        event_type="search.saved.created",
        event_payload={"saved_search_id": saved.id},
    )
    return saved
