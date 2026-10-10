from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.tag_schema import (
    ReadTagSchema, CreateTagSchema, AfterCreateTagSchema, AfterDeleteTagSchema,             TagFilterSchema, TagPaginationSchema, UpdateTagSchema, AfterUpdateTagSchema
)
from app.repositories import tag_repository
from app.core.helpers import admin_required


router = APIRouter(
    prefix="/api/tags", tags=["Tags"]
)


@router.get("/", response_model=TagPaginationSchema, status_code=status.HTTP_200_OK)
def get_tags(filters: TagFilterSchema = Depends(), db: Session = Depends(get_db)) -> TagPaginationSchema:
    tags, total = tag_repository.get_all(db, filters)

    return {
        "tags": tags,
        "total": total,
        "page": filters.offset // filters.limit + 1,
        "limit": filters.limit
    }


@router.post("/", dependencies=[Depends(admin_required)], response_model=AfterCreateTagSchema, status_code=status.HTTP_201_CREATED)
def create_tag(data: CreateTagSchema, db: Session = Depends(get_db)) -> AfterCreateTagSchema:
    new_tag = tag_repository.create(db, data)
    return {
        "message": "Tag created successfully",
        "tag": new_tag
    }


@router.get("/{tag_id}", response_model=ReadTagSchema, status_code=status.HTTP_200_OK)
def get_tag(tag_id: int, db: Session = Depends(get_db)) -> ReadTagSchema:
    return tag_repository.get_by_id(db, tag_id)


@router.put('/{tag_id}', dependencies=[Depends(admin_required)], response_model=AfterUpdateTagSchema, status_code=status.HTTP_200_OK)
def update_tag(tag_id: int, data: UpdateTagSchema, db: Session = Depends(get_db)) -> AfterUpdateTagSchema:
    tag = tag_repository.update(db, tag_id, data)
    return {
        "message": "Tag updated successfully",
        "tag": tag
    }


@router.delete("/{tag_id}", dependencies=[Depends(admin_required)], status_code=status.HTTP_200_OK, response_model=AfterDeleteTagSchema)
def delete_tag(tag_id: int, db: Session = Depends(get_db)) -> AfterDeleteTagSchema:
    tag = tag_repository.delete(db, tag_id)
    return {
        "message": f"Tag with id {tag.id} deleted successfully"
    }
