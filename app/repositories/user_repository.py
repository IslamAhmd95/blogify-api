from fastapi import HTTPException, status
from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session, selectinload

from app.models.user import User
from app.models.profile import Profile
from app.models.post import Post
from app.models.tag import Tag
from app.schemas.user_schema import UpdatePassword, UserFilter
from app.core.hashing import hash_password, verify_password
from app.core.enums import RoleEnum, OrderEnum
from app.core.helpers import check_email_exists, check_username_exists
from app.core.token_store import revoke_all_user_tokens


def get_user_by_id(db: Session, user_id: int) -> User:
    user = db.execute(
        select(User)
        .options(selectinload(User.profile))
        .options(selectinload(User.followers))
        .options(selectinload(User.following))
        .where(User.id == user_id)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


def get_posts_by_user_id(db: Session, filters: UserFilter, user_id: int) -> dict:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    total = db.scalar(
        select(func.count()).select_from(Post)
        .where(Post.author_id == user_id)
    )

    posts = db.scalars(
            select(Post)
            .options(selectinload(Post.tags).load_only(Tag.id, Tag.name))
            .where(Post.author_id == user_id)
            .order_by(Post.id if filters.order == OrderEnum.ASC else desc(Post.id))
            .offset(filters.offset)
            .limit(filters.limit)
        ).all()

    return total, posts


def update_me(db: Session, user_id: int, data) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    

    try:
        update_data = data.model_dump(exclude_unset=True)

        if "email" in update_data and check_email_exists(update_data['email'], db, user):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
            
        
        if "username" in update_data and check_username_exists(update_data['username'], db, user):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        for key, value in update_data.items():
            if key == "bio":
                if not user.profile:
                    user.profile = Profile(bio=value)
                else:
                    user.profile.bio = value
            else:
                setattr(user, key, value)

        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while updating the user: {str(e)}.")


def update_password(db: Session, user_id: int, data: UpdatePassword) -> dict:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if not verify_password(data.current_password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")
    
    try:
        user.password = hash_password(data.new_password)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while updating the password: {str(e)}.")

    # if the password was changed because the account was compromised, the attacker's sessions must die too
    revoke_all_user_tokens(user.id)
    

def get_all_users(db: Session, filters: UserFilter):
    total = db.scalar(
        select(func.count()).select_from(User)
        .where(User.role == RoleEnum.USER)
    )

    users = db.scalars(select(User)
                      .options(selectinload(User.profile))
                      .where(User.role == RoleEnum.USER)
                      .order_by(User.id.asc() if filters.order == OrderEnum.ASC else User.id.desc())
                      .offset(filters.offset).limit(filters.limit)
                    ).all()
    
    return total, users


def get_followers(db: Session, user_id: int):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    return user


def get_following(db: Session, user_id: int):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    return user


def follow_user(db: Session, current_user, target_user_id: int) -> dict:
    db_user = db.get(User, current_user.id)
    target_user = db.get(User, target_user_id)

    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {target_user_id} not found.")

    if target_user in db_user.following:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already following this user.")

    try:
        db_user.following.append(target_user)
        db.commit()
        return target_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while following the user: {str(e)}.")
    

def unfollow_user(db: Session, current_user, target_user_id: int) -> dict:
    db_user = db.get(User, current_user.id)
    target_user = db.get(User, target_user_id)

    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {target_user_id} not found.")

    if target_user not in db_user.following:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You're already not following this user.")

    try:
        db_user.following.remove(target_user)
        db.commit()
        return target_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while following the user: {str(e)}.")


def delete_user(db: Session, user_id: int) -> str:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    if user.role == RoleEnum.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete an admin user.")

    try:
        db.delete(user)
        db.commit()
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while deleting the user: {str(e)}.")

