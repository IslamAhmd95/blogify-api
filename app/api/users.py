from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories import user_repository
from app.core.helpers import admin_required, get_current_user
from app.schemas.user_schema import (
    ReadUser,
    AfterDeleteUser,
    UpdateMe,
    AfterUpdateMe,
    UpdatePassword,
    AfterUpdatePassword,
    AfterFollowUser,
    AfterUnfollowUser,
    ReadFollowers,
    ReadFollowing,
    UserFilter,
    ReadUserPostsSchema,
    ReadAllUsersSchema
)


router = APIRouter(
    prefix="/api/users", tags=["Users"]
)


@router.get('/me', response_model=ReadUser)
def show_me(current_user: ReadUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return user_repository.get_user_by_id(db, current_user.id)


@router.put('/me', response_model=AfterUpdateMe)
def update_me(data: UpdateMe, current_user: ReadUser = Depends(get_current_user), db: Session = Depends(get_db)):
    user = user_repository.update_me(db, current_user.id, data)
    return {"success": True, "message": "User updated successfully.", "user": ReadUser.model_validate(user)}


@router.get('/me/posts', response_model=ReadUserPostsSchema)
def get_my_posts(filters: UserFilter = Depends(), current_user: ReadUser = Depends(get_current_user), db: Session = Depends(get_db)):
    total, posts = user_repository.get_posts_by_user_id(
        db, filters, current_user.id)
    return {
        "posts": posts,
        "total": total,
        "page": filters.offset // filters.limit + 1,
        "limit": filters.limit
    }


@router.get('/{user_id}/posts', response_model=ReadUserPostsSchema)
def get_user_posts(user_id: int, filters: UserFilter = Depends(), db: Session = Depends(get_db)):
    total, posts = user_repository.get_posts_by_user_id(db, filters, user_id)
    return {
        "posts": posts,
        "total": total,
        "page": filters.offset // filters.limit + 1,
        "limit": filters.limit
    }


@router.put('/me/update-password', response_model=AfterUpdatePassword)
def update_password(data: UpdatePassword, current_user: ReadUser = Depends(get_current_user), db: Session = Depends(get_db)):
    user_repository.update_password(db, current_user.id, data)
    return {"success": True, "message": "Password updated successfully."}


@router.get('/', dependencies=[Depends(admin_required)], response_model=ReadAllUsersSchema)
def get_all_users(filters: UserFilter = Depends(), db: Session = Depends(get_db)):
    total, users = user_repository.get_all_users(db, filters)
    return {
        "users": users,
        "total": total,
        "page": filters.offset // filters.limit + 1,
        "limit": filters.limit
    }


@router.get('/{user_id}', response_model=ReadUser)
def show(user_id: int, db: Session = Depends(get_db)):
    return user_repository.get_user_by_id(db, user_id)


@router.get('/me/followers', response_model=ReadFollowers)
def get_my_followers(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user = user_repository.get_followers(db, current_user.id)
    return {"followers": user.followers}


@router.get('/me/following', response_model=ReadFollowing)
def get_my_following(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user = user_repository.get_following(db, current_user.id)
    return {"following": user.following}


@router.get("/{user_id}/followers", response_model=ReadFollowers)
def get_followers(user_id: int, db: Session = Depends(get_db)):
    user = user_repository.get_followers(db, user_id)
    return {"followers": user.followers}


@router.get("/{user_id}/following", response_model=ReadFollowing)
def get_following(user_id: int, db: Session = Depends(get_db)):
    user = user_repository.get_following(db, user_id)
    return {"following": user.following}


@router.post('/{target_user_id}/follow', response_model=AfterFollowUser)
def follow_user(target_user_id: int, current_user: ReadUser = Depends(get_current_user), db: Session = Depends(get_db)):
    user = user_repository.follow_user(db, current_user, target_user_id)
    return {"success": True, "message": f"Now you are following {user.username}."}


@router.delete('/{target_user_id}/unfollow', response_model=AfterUnfollowUser)
def unfollow_user(target_user_id: int, current_user: ReadUser = Depends(get_current_user), db: Session = Depends(get_db)):
    user = user_repository.unfollow_user(db, current_user, target_user_id)
    return {"success": True, "message": f"Now you are not following {user.username}."}


@router.delete('/{user_id}', dependencies=[Depends(admin_required)], response_model=AfterDeleteUser)
def delete(user_id: int, db: Session = Depends(get_db)):
    user = user_repository.delete_user(db, user_id)
    return {"success": True, "message": f"User {user.username} deleted successfully."}
