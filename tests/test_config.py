"""
Tests for configuration management endpoints.
"""

import pytest

from app.db.models import ServiceConfig, ConfigVersion


class TestHealthCheck:
    """Tests for the health check endpoint."""

    def test_health_check(self, client):
        """Test that the health check endpoint returns status OK."""
        response = client.get("/config/health")
        assert response.status_code == 200
        data = response.json()
        assert data["api_status"] == "ok"
        assert data["db_status"] == "connected"


class TestConfigUpdate:
    """Tests for configuration creation/update endpoint."""

    def test_create_config(self, client, normal_user, auth_headers_normal, db_session):
        """Test creating a new configuration."""
        response = client.post(
            "/config/update",
            headers=auth_headers_normal,
            json={
                "name": "my-service",
                "config": {"api_key": "test123", "timeout": 30}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "my-service"
        assert data["config"]["api_key"] == "test123"
        assert data["user_id"] == normal_user.id

        # Verify it's in the database
        config = db_session.query(ServiceConfig).filter_by(name="my-service").first()
        assert config is not None
        assert config.user_id == normal_user.id

    def test_update_existing_config(self, client, normal_user, auth_headers_normal, db_session):
        """Test updating an existing configuration."""
        # First, create the config
        db_session.add(ServiceConfig(
            name="existing-service",
            config={"api_key": "oldkey", "timeout": 20},
            user_id=normal_user.id
        ))
        db_session.commit()

        # Now update it
        response = client.post(
            "/config/update",
            headers=auth_headers_normal,
            json={
                "name": "existing-service",
                "config": {"api_key": "newkey", "timeout": 45}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "existing-service"
        assert data["config"]["api_key"] == "newkey"
        assert data["config"]["timeout"] == 45

        # Verify update in database
        config = db_session.query(ServiceConfig).filter_by(name="existing-service").first()
        assert config.config["api_key"] == "newkey"
        assert config.config["timeout"] == 45

    def test_update_creates_version(self, client, normal_user, auth_headers_normal, db_session):
        """Test if updating a config creates a new version entry."""
        response = client.post(
            "/config/update",
            headers=auth_headers_normal,
            json={
                "name": "versioned-service",
                "config": {"data": "v1"}
            }
        )

        # Check version was created
        versions = db_session.query(ConfigVersion).filter_by(
            service_name="versioned-service",
            user_id=normal_user.id
        ).all()

        assert len(versions) == 1
        assert versions[0].version == 1
        assert versions[0].config["data"] == "v1"

    def test_update_without_auth(self, client):
        """Test that updating config without authentication fails."""
        response = client.post(
            "/config/update",
            json={
                "name": "unauth-service",
                "config": {"key": "value"}
            }
        )

        assert response.status_code == 401

    def test_user_cannot_update_others_users_config(self, client, normal_user, admin_user, auth_headers_normal, db_session):
        """Test that a normal user cannot update another user's configuration."""
        # Admin creates a config
        db_session.add(ServiceConfig(
            name="admin-service",
            config={"admin_key": "secret"},
            user_id=admin_user.id
        ))
        db_session.commit()

        # Normal user attempts to update admin's config
        response = client.post(
            "/config/update",
            headers=auth_headers_normal,
            json={
                "name": "admin-service",
                "config": {"admin_key": "hacked"}
            }
        )

        # Try to update as a normal user, it should create their own config instead
        assert response.status_code == 200
        assert response.json()["user_id"] == normal_user.id

        # Verify that admin's config was not changed
        admin_config = db_session.query(ServiceConfig).filter_by(
            name="admin-service",
            user_id=admin_user.id
        ).first()
        assert admin_config.config["admin_key"] == "secret"


class TestConfigRetrieval:
    """Tests for configuration retrieval endpoint."""

    def test_retrieve_config(self, client, normal_user, auth_headers_normal, db_session):
        """Test retrieving an existing configuration."""
        # Create a config to retrieve
        db_session.add(ServiceConfig(
            name="retrieve-service",
            config={"setting": "value1"},
            user_id=normal_user.id
        ))
        db_session.commit()

        response = client.get(
            "/config/get?service=retrieve-service",
            headers=auth_headers_normal
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "retrieve-service"
        assert data["config"]["setting"] == "value1"
        assert data["user_id"] == normal_user.id

    def test_retrieve_nonexistent_config(self, client, normal_user, auth_headers_normal):
        """Test retrieving a non-existent configuration returns 404."""
        response = client.get(
            "/config/get?service=nonexistent-service",
            headers=auth_headers_normal
        )

        assert response.status_code == 404
        assert "Service config not found" in response.json()["detail"]

    def test_list_configs(self, client, normal_user, auth_headers_normal, db_session):
        """Test listing all configs for a user."""
        # Create multiple configs
        configs = [
            ServiceConfig(name="service1", config={"a": 1}, user_id=normal_user.id),
            ServiceConfig(name="service2", config={"b": 2}, user_id=normal_user.id)
        ]
        for c in configs:
            db_session.add(c)
        db_session.commit()

        response = client.get("/config/list", headers=auth_headers_normal)

        assert response.status_code == 200
        data = response.json()
        assert len(data["configs"]) == 2
        names = [c["name"] for c in data["configs"]]
        assert "service1" in names
        assert "service2" in names

    def test_list_only_shows_own_configs(self, client, normal_user, admin_user, auth_headers_normal, db_session):
        """Test that normal users only see their own configs."""
        # Create configs for both users
        db_session.add(ServiceConfig(name="user-service", config={}, user_id=normal_user.id))
        db_session.add(ServiceConfig(name="admin-service", config={}, user_id=admin_user.id))
        db_session.commit()

        response = client.get("/config/list", headers=auth_headers_normal)

        data = response.json()
        assert len(data["configs"]) == 1
        assert data["configs"][0]["name"] == "user-service"


class TestConfigDelete:
    """Tests for configuration deletion endpoint."""

    def test_delete_own_config(self, client, normal_user, auth_headers_normal, db_session):
        """Test deleting own configuration."""
        config = ServiceConfig(
            name="to-delete",
            config={"data": "value"},
            user_id=normal_user.id
        )
        db_session.add(config)
        db_session.commit()

        response = client.delete(
            "/config/delete/to-delete",
            headers=auth_headers_normal
        )

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["detail"]

        # Verify it's gone
        deleted = db_session.query(ServiceConfig).filter_by(name="to-delete").first()
        assert deleted is None

    def test_delete_nonexistent_config(self, client, auth_headers_normal):
        """Test deleting a config that doesn't exist."""
        response = client.delete(
            "/config/delete/nonexistent",
            headers=auth_headers_normal
        )
        assert response.status_code == 404


class TestAdminPermissions:
    """Tests for admin-only configuration management features."""

    def test_admin_can_retrieve_others_config(self, client, normal_user, admin_user, auth_headers_admin, db_session):
        """Test that an admin can retrieve another user's configuration."""
        # Normal user creates a config
        db_session.add(ServiceConfig(
            name="user-service",
            config={"user_key": "user_value"},
            user_id=normal_user.id
        ))
        db_session.commit()

        response = client.get(
            f"/config/get?service=user-service&target_user_id={normal_user.id}",
            headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "user-service"
        assert data["config"]["user_key"] == "user_value"
        assert data["user_id"] == normal_user.id

    def test_admin_can_get_other_user_config(self, client, normal_user, auth_headers_admin, db_session):
        """Test that admin can retrieve another user's config."""
        config = ServiceConfig(
            name="user-service",
            config={"secret": "data"},
            user_id=normal_user.id
        )
        db_session.add(config)
        db_session.commit()

        response = client.get(
            f"/config/get?service=user-service&target_user_id={normal_user.id}",
            headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == normal_user.id

    def test_admin_can_update_other_user_config(self, client, normal_user, auth_headers_admin, db_session):
        """Test that admin can update another user's config."""
        config = ServiceConfig(
            name="user-service",
            config={"version": 1},
            user_id=normal_user.id
        )
        db_session.add(config)
        db_session.commit()

        response = client.post(
            f"/config/update?target_user_id={normal_user.id}",
            headers=auth_headers_admin,
            json={
                "name": "user-service",
                "config": {"version": 2}
            }
        )

        assert response.status_code == 200
        # Config still belongs to normal user
        assert response.json()["user_id"] == normal_user.id
        assert response.json()["config"]["version"] == 2