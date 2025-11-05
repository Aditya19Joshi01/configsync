"""
Tests for authentication endpoints: register, login, logout.
"""
import pytest
from app.db.models import User, RevokedToken


class TestRegistration:
    """Tests for user registration endpoint."""

    def test_register_new_user(self, client, db_session):
        """Test successful user registration."""
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "securepass123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "user"  # default role
        assert "id" in data

        # Verify user was created in database
        user = db_session.query(User).filter_by(username="newuser").first()
        assert user is not None
        assert user.email == "newuser@example.com"

    def test_register_with_admin_role(self, client, db_session):
        """Test registering a user with admin role."""
        response = client.post(
            "/auth/register",
            json={
                "username": "newadmin",
                "email": "newadmin@example.com",
                "password": "adminpass123",
                "role": "admin"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"

    def test_register_existing_username(self, client, normal_user):
        """Test that registering with an existing username fails."""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",  # already exists
                "email": "different@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 400
        assert "Username already exists" in response.json()["detail"]

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format."""
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "not-an-email",
                "password": "password123"
            }
        )

        assert response.status_code == 422  # Validation error


class TestLogin:
    """Tests for user login endpoint."""

    def test_login_success(self, client, normal_user):
        """Test successful login returns a token."""
        response = client.post(
            "/auth/login",
            data={
                "username": "testuser",
                "password": "testpass123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "jti" in data
        assert "expires_at" in data

    def test_login_wrong_password(self, client, normal_user):
        """Test login fails with incorrect password."""
        response = client.post(
            "/auth/login",
            data={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login fails for non-existent user."""
        response = client.post(
            "/auth/login",
            data={
                "username": "nonexistent",
                "password": "password123"
            }
        )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]


class TestLogout:
    """Tests for user logout endpoint."""

    def test_logout_success(self, client, normal_user, auth_headers_normal):
        """Test successful logout revokes the token."""
        response = client.post("/auth/logout", headers=auth_headers_normal)

        assert response.status_code == 200
        assert response.json()["msg"] == "logged out"

    def test_logout_revokes_token(self, client, db_session, normal_user, normal_user_token, auth_headers_normal):
        """Test that logout adds token to revoked tokens table."""
        # Logout
        client.post("/auth/logout", headers=auth_headers_normal)

        # Check that token is revoked
        from app.core.security import decode_access_token
        payload = decode_access_token(normal_user_token)
        jti = payload["jti"]

        revoked = db_session.query(RevokedToken).filter_by(jti=jti).first()
        assert revoked is not None
        assert revoked.user_id == normal_user.id

    def test_cannot_use_revoked_token(self, client, auth_headers_normal):
        """Test that a revoked token cannot be used for authenticated requests."""
        # Logout (revokes token)
        client.post("/auth/logout", headers=auth_headers_normal)

        # Try to use the same token
        response = client.get("/config/list", headers=auth_headers_normal)
        assert response.status_code == 401
        assert "Token revoked" in response.json()["detail"]

    def test_logout_without_token(self, client):
        """Test logout fails without authentication."""
        response = client.post("/auth/logout")
        assert response.status_code == 401