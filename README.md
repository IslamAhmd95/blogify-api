# 📝 FastAPI Blog

## 📘 Overview

**FastAPI Blog** is a fully featured backend-only, Dockerized blogging system built using **FastAPI**, **SQLAlchemy ORM**, and **Pydantic**. The project follows a clean and scalable architecture using the **Repository Pattern**, **eager loading for optimized queries**, and a well-structured module layout suitable for real-world production applications.

This backend handles user authentication, posts, comments, likes, tags, profiles, and a follow system between users. It demonstrates how to implement complete business logic in a clean and maintainable way.

---

## 🌟 Key Features

### 👤 **User Management**

* Create, update, delete users
* User profiles
* Follow/unfollow system
* Secure password hashing

### 📝 **Posts & Comments**

* Full CRUD for posts
* Comment system with CRUD
* Like/unlike both posts and comments
* Relation-based querying

### 🏷️ **Tags System**

* Add tags to posts
* List posts by tag
* Many-to-many relationships

### ❤️ **Likes System**

* Users can like/unlike posts and comments
* Prevent multiple likes from same user

### 🔐 **Authentication**

* JWT-based authentication
* OAuth2 password flow
* Access token creation & validation

### ⚡ **Performance Techniques**

* **Eager loading** for efficient queries (selectinload/joinedload)
* Clean repository abstraction for data access

### 🏗️ **Architecture Highlights**

* Repository pattern
* Models and schemas separation
* Modular API routes
* Centralized database session handling

---

## 📂 Project Structure

```
fastapi-blog/
│
├── app/
│   ├── api/                # All API route files
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── posts.py
│   │   ├── comments.py
│   │   └── tags.py
│   │
│   ├── core/               # Core system utilities & configs
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── enums.py
│   │   ├── events.py
│   │   ├── hashing.py
│   │   ├── helpers.py
│   │   ├── oauth2.py
│   │   └── token.py
│   │
│   ├── models/             # SQLAlchemy ORM models
│   │   ├── users.py
│   │   ├── profile.py
│   │   ├── posts.py
│   │   ├── comments.py
│   │   ├── tags.py
│   │   ├── users_followers.py
│   │   ├── post_tags.py
│   │   ├── post_likes.py
│   │   └── comment_likes.py
│   │
│   ├── repositories/       # Repository pattern implementation
│   │   ├── auth_repository.py
│   │   ├── user_repository.py
│   │   ├── post_repository.py
│   │   ├── comment_repository.py
│   │   └── tag_repository.py
│   │
│   ├── schemas/            # Pydantic schemas for validation/response
│       ├── auth_schema.py
│       ├── user_schema.py
│       ├── post_schema.py
│       ├── comment_schema.py
│       └── tag_schema.py
│
├── alembic/                # Database migrations
├── scripts/
│   └── seed.py             # Database seeding script
│
├── .env                    # Environment configuration
├── .env.example
├── .dockerignore           # Docker ignore file
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose configuration
├── alembic.ini
├── main.py                 # FastAPI entry point
└── requirements.txt        # Dependencies
```

---

## 🚀 Getting Started

### 1. **Clone the repository**

```
git clone https://github.com/IslamAhmd95/fastapi-blog
cd fastapi-blog/
```

### 2. **Create and activate a virtual environment**

```
python3 -m venv venv
source venv/bin/activate
```

### 3. **Install dependencies**

```
pip install -r requirements.txt
```

### 4. **Setup environment variables and secret**

```
cp .env.example .env
```

### 5. **Apply migrations**

```
alembic upgrade head
```

### 6. **Seed the database**

```
python -m scripts.seed
```

### 7. **Run the development server**

```
uvicorn main:app --reload
```

---

## 🐳 Docker Setup

### Prerequisites

* Docker installed on your system
* Docker Compose installed on your system

### Quick Start with Docker

#### 1. **Clone the repository**

```
git clone https://github.com/IslamAhmd95/blogify-api
cd blogify-api/
```

#### 2. **Setup environment variables**

```
cp .env.example .env
```

Make sure to configure your `.env` file with the appropriate database credentials and other settings.

#### 3. **Build and start containers**

```
docker-compose up --build
```

This will:
* Build the FastAPI backend image
* Start MySQL 8.0 database container
* Start the FastAPI backend container
* Automatically create the database volume for data persistence

#### 4. **Apply migrations**

In a new terminal, run migrations inside the backend container:

```
docker-compose exec backend alembic upgrade head
```

#### 5. **Seed the database (optional)**

```
docker-compose exec backend python -m scripts.seed
```

#### 6. **Access the application**

* **API**: http://localhost:8001
* **API Documentation**: http://localhost:8001/docs
```

---
