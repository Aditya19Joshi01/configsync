"""
Test configuration and fixtures for pytest.
This file is automatically loaded by pytest and provides reusable test utilities.
"""
import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set testing flag before importing app
os.environ["TESTING"] = "true"

from app.main import app
from app.db.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.db.models import User
from datetime import timedelta

# Use in-memory SQLite database for tests (fast and isolated)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with special settings for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """
    Automatically sets up and tears down the database for each test.
    This ensures complete isolation between tests.
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop all tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(setup_test_db):
    """
    Creates a fresh database session for each test.
    This ensures tests don't interfere with each other.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    Provides a TestClient with a test database.
    Use this to make API requests in your tests.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db

    # Disable the startup event that creates tables with production DB
    # We already create tables in setup_test_db fixture
    app.router.on_startup = []

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def normal_user(db_session):
    """
    Creates a normal (non-admin) user for testing.
    """
    user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password=get_password_hash("testpass123"),
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """
    Creates an admin user for testing admin-only features.
    """
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        role="admin"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def normal_user_token(normal_user):
    """
    Generates an authentication token for the normal user.
    """
    token, jti, expires = create_access_token(
        data={"sub": normal_user.username},
        expires_delta=timedelta(minutes=60)
    )
    return token


@pytest.fixture
def admin_user_token(admin_user):
    """
    Generates an authentication token for the admin user.
    """
    token, jti, expires = create_access_token(
        data={"sub": admin_user.username},
        expires_delta=timedelta(minutes=60)
    )
    return token


@pytest.fixture
def auth_headers_normal(normal_user_token):
    """
    Returns authorization headers for a normal user.
    Use this in API requests that require authentication.
    """
    return {"Authorization": f"Bearer {normal_user_token}"}


@pytest.fixture
def auth_headers_admin(admin_user_token):
    """
    Returns authorization headers for an admin user.
    """
    return {"Authorization": f"Bearer {admin_user_token}"}