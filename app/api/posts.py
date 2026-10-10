from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.oauth2 import get_current_user
from app.repositories import post_repository
from app.schemas.post_schema import (
    ReadPostSchema,
    CreatePostSchema,
    UpdatePostSchema,
    AfterCreatePostSchema,
    AfterUpdatePostSchema,
    AfterDeletePostSchema,
    LikeResponseSchema,
    GetPostLikesSchema,
    PostFilterSchema,
    ReadOnePostSchema,
    CommentFilterSchema,
    ReadCommentsSchema,
    AfterCreateCommentSchema,
    CreateCommentSchema
)
from app.schemas.user_schema import ReadUser


router = APIRouter(
    prefix="/api/posts",
    tags=["Posts"]
)

# Get all posts with optional filters
@router.get("/", response_model=ReadPostSchema, status_code=status.HTTP_200_OK)
def get_posts(filters: PostFilterSchema = Depends(), db: Session = Depends(get_db)):
    posts, total = post_repository.get_all(db, filters)
    return {
        "posts": posts,
        "total": total,
        "page": filters.offset // filters.limit + 1,
        "limit": filters.limit
    }

# Get a specific post by ID
@router.get("/{post_id}", response_model=ReadOnePostSchema, status_code=status.HTTP_200_OK)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = post_repository.get_by_id(db, post_id)
    return {"post": post}

# Create a new post
@router.post("/", response_model=AfterCreatePostSchema, status_code=status.HTTP_201_CREATED)
def create_post(
    data: CreatePostSchema,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    new_post = post_repository.create_post(db, data, current_user)
    return {"post": new_post, "message": "Post created successfully"}


# Update a specific post
@router.put("/{post_id}", response_model=AfterUpdatePostSchema, status_code=status.HTTP_200_OK)
def update_post(
    post_id: int,
    data: UpdatePostSchema,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    post = post_repository.update(db, post_id, data, current_user)
    return {
        "post": post,
        "message": "Post updated successfully"
    }


# Delete a specific post
@router.delete("/{post_id}", response_model=AfterDeletePostSchema, status_code=status.HTTP_200_OK)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    post = post_repository.delete(db, post_id, current_user)
    return {
        "message": f"Post with id {post.id} deleted successfully"
    }

# Like a specific post
@router.post("/{post_id}/like", response_model=LikeResponseSchema, status_code=status.HTTP_200_OK)
def like_post(post_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    post_repository.like_post(db, post_id, current_user.id)
    return {"message": "You liked the post successfully"}

# Unlike a post
@router.delete("/{post_id}/unlike", response_model=LikeResponseSchema, status_code=status.HTTP_200_OK)
def unlike_post(post_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    post_repository.unlike_post(db, post_id, current_user.id)
    return {"message": "You unliked the post successfully"}


# Get likes for a specific post
@router.get("/{post_id}/likes", response_model=GetPostLikesSchema)
def get_post_likes(post_id: int, db: Session = Depends(get_db)):
    post = post_repository.get_post_likes(db, post_id)
    return {
        "total_likes": len(post.liked_by),
        "liked_users": post.liked_by
    }


# Get comments for a specific post
@router.get('/{post_id}/comments', dependencies=[Depends(get_current_user)], status_code=status.HTTP_200_OK, response_model=ReadCommentsSchema)
def get_comments(post_id: int, filters: CommentFilterSchema = Depends(), db: Session = Depends(get_db)):
    comments, total = post_repository.get_comments(db, post_id, filters)
    return {
        "comments": comments,
        "total": total,
        "page": filters.offset // filters.limit + 1,
        "limit": filters.limit
    }


# Create a comment for a specific post
@router.post('/{post_id}/comments', status_code=status.HTTP_201_CREATED, response_model=AfterCreateCommentSchema)
def create_comment(post_id: int, comment_data: CreateCommentSchema, current_user: ReadUser = Depends(get_current_user), db: Session = Depends(get_db)):
    new_comment = post_repository.create_comment(db, comment_data, post_id, current_user.id)
    return {"message": "Comment created successfully", "comment": new_comment}