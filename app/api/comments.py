from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.oauth2 import get_current_user
from app.repositories import comment_repository
from app.schemas.user_schema import ReadUser
from app.schemas.comment_schema import (
    ReadCommentSchema,
    UpdateCommentSchema,
    AfterUpdateCommentSchema,
    AfterDeleteCommentSchema,
    LikeCommentSchema,
    GetCommentLikesSchema
)


router = APIRouter(
    prefix="/api/comments",
    tags=["comments"]
)

# get specific comment


@router.get('/{comment_id}', status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user)], response_model=ReadCommentSchema)
def get_comment(comment_id: int, db: Session = Depends(get_db)):
    comment = comment_repository.get_comment_by_id(db, comment_id)
    return {"comment": comment}

# update comment


@router.put('/{comment_id}', status_code=status.HTTP_200_OK, response_model=AfterUpdateCommentSchema)
def update_comment(comment_id: int, comment_data: UpdateCommentSchema, current_user: ReadUser = Depends(get_current_user), db: Session = Depends(get_db)):
    comment = comment_repository.update(
        db, comment_id, comment_data, current_user.id)
    return {"message": "Comment updated successfully", "comment": comment}

# delete comment


@router.delete('/{comment_id}', status_code=status.HTTP_200_OK, response_model=AfterDeleteCommentSchema)
def delete_comment(comment_id: int, current_user: ReadUser = Depends(get_current_user), db: Session = Depends(get_db)):
    comment = comment_repository.delete(db, comment_id, current_user.id)
    return {"message": f"Comment with id {comment.id} has been deleted."}

# like a comment


@router.post('/{comment_id}/like', status_code=status.HTTP_200_OK, response_model=LikeCommentSchema)
def like_comment(comment_id: int, current_user: ReadUser = Depends(get_current_user), db: Session = Depends(get_db)):
    comment_repository.like_comment(db, comment_id, current_user)
    return {"message": "You liked the comment successfully"}


# delete a comment
@router.delete('/{comment_id}/unlike', status_code=status.HTTP_200_OK, response_model=LikeCommentSchema)
def unlike_comment(comment_id: int, current_user: ReadUser = Depends(get_current_user), db: Session = Depends(get_db)):
    comment_repository.unlike_comment(db, comment_id, current_user)
    return {"message": "You unliked the comment successfully"}

# get comment likes


@router.get('/{comment_id}/likes', status_code=status.HTTP_200_OK, response_model=GetCommentLikesSchema)
def get_comment_likes(comment_id: int, db: Session = Depends(get_db)):
    comment = comment_repository.get_comment_likes(db, comment_id)
    return {
        "total_likes": len(comment.liked_by),
        "liked_users": comment.liked_by
    }
