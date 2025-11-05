"""
Tests for configuration versioning features: versions, rollback, diff.
"""
import pytest
from app.db.models import ServiceConfig, ConfigVersion


class TestVersionListing:
    """Tests for listing configuration versions."""

    def test_list_versions_empty(self, client, auth_headers_normal):
        """Test listing versions when none exist."""
        response = client.get(
            "/config/versions/nonexistent",
            headers=auth_headers_normal
        )

        assert response.status_code == 200
        data = response.json()
        assert data["service_name"] == "nonexistent"
        assert len(data["versions"]) == 0

    def test_list_versions_multiple(self, client, normal_user, auth_headers_normal, db_session):
        """Test listing multiple versions."""
        # Create service config and versions manually
        config = ServiceConfig(
            name="versioned-app",
            config={"version": 3},
            user_id=normal_user.id
        )
        db_session.add(config)

        versions = [
            ConfigVersion(service_name="versioned-app", version=1, config={"version": 1}, user_id=normal_user.id),
            ConfigVersion(service_name="versioned-app", version=2, config={"version": 2}, user_id=normal_user.id),
            ConfigVersion(service_name="versioned-app", version=3, config={"version": 3}, user_id=normal_user.id)
        ]
        for v in versions:
            db_session.add(v)
        db_session.commit()

        response = client.get(
            "/config/versions/versioned-app",
            headers=auth_headers_normal
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["versions"]) == 3
        # Should be in descending order (newest first)
        assert data["versions"][0]["version"] == 3
        assert data["versions"][2]["version"] == 1


class TestRollback:
    """Tests for rolling back to previous versions."""

    def test_rollback_to_previous_version(self, client, normal_user, auth_headers_normal, db_session):
        """Test rolling back to a previous configuration version."""
        # Create config with version history
        config = ServiceConfig(
            name="app",
            config={"version": 2, "feature": "new"},
            user_id=normal_user.id
        )
        db_session.add(config)

        v1 = ConfigVersion(
            service_name="app",
            version=1,
            config={"version": 1, "feature": "old"},
            user_id=normal_user.id
        )
        v2 = ConfigVersion(
            service_name="app",
            version=2,
            config={"version": 2, "feature": "new"},
            user_id=normal_user.id
        )
        db_session.add(v1)
        db_session.add(v2)
        db_session.commit()

        # Rollback to version 1
        response = client.post(
            f"/config/rollback/app?target_version_id={v1.id}",
            headers=auth_headers_normal
        )

        assert response.status_code == 200
        data = response.json()
        assert data["config"]["version"] == 1
        assert data["config"]["feature"] == "old"

        # Verify config was updated in DB
        db_session.refresh(config)
        assert config.config["version"] == 1

    def test_rollback_creates_new_version(self, client, normal_user, auth_headers_normal, db_session):
        """Test that rollback creates a new version entry."""
        config = ServiceConfig(name="app", config={"v": 2}, user_id=normal_user.id)
        db_session.add(config)

        v1 = ConfigVersion(service_name="app", version=1, config={"v": 1}, user_id=normal_user.id)
        v2 = ConfigVersion(service_name="app", version=2, config={"v": 2}, user_id=normal_user.id)
        db_session.add_all([v1, v2])
        db_session.commit()

        # Rollback
        client.post(
            f"/config/rollback/app?target_version_id={v1.id}",
            headers=auth_headers_normal
        )

        # Should now have 3 versions (v1, v2, and the rollback)
        versions = db_session.query(ConfigVersion).filter_by(
            service_name="app",
            user_id=normal_user.id
        ).order_by(ConfigVersion.version).all()

        assert len(versions) == 3
        assert versions[2].version == 3
        assert versions[2].config == v1.config  # Contains v1's config

    def test_rollback_nonexistent_version(self, client, normal_user, auth_headers_normal, db_session):
        """Test rollback fails for non-existent version."""
        config = ServiceConfig(name="app", config={}, user_id=normal_user.id)
        db_session.add(config)
        db_session.commit()

        response = client.post(
            "/config/rollback/app?target_version_id=99999",
            headers=auth_headers_normal
        )

        assert response.status_code == 404

    def test_rollback_nonexistent_config(self, client, auth_headers_normal):
        """Test rollback fails when config doesn't exist."""
        response = client.post(
            "/config/rollback/nonexistent?target_version_id=1",
            headers=auth_headers_normal
        )

        assert response.status_code == 404


class TestVersionDiff:
    """Tests for comparing configuration versions."""

    def test_diff_two_versions(self, client, normal_user, auth_headers_normal, db_session):
        """Test computing diff between two versions."""
        v1 = ConfigVersion(
            service_name="app",
            version=1,
            config={"setting1": "value1", "setting2": "old"},
            user_id=normal_user.id
        )
        v2 = ConfigVersion(
            service_name="app",
            version=2,
            config={"setting1": "value1", "setting2": "new", "setting3": "added"},
            user_id=normal_user.id
        )
        db_session.add_all([v1, v2])
        db_session.commit()

        response = client.get(
            f"/config/diff/app?version1_id={v1.id}&version2_id={v2.id}",
            headers=auth_headers_normal
        )

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "app"
        assert data["version1"] == v1.id
        assert data["version2"] == v2.id
        assert "diff" in data

    def test_diff_identical_versions(self, client, normal_user, auth_headers_normal, db_session):
        """Test diff of identical configs shows no changes."""
        same_config = {"a": 1, "b": 2}
        v1 = ConfigVersion(service_name="app", version=1, config=same_config, user_id=normal_user.id)
        v2 = ConfigVersion(service_name="app", version=2, config=same_config, user_id=normal_user.id)
        db_session.add_all([v1, v2])
        db_session.commit()

        response = client.get(
            f"/config/diff/app?version1_id={v1.id}&version2_id={v2.id}",
            headers=auth_headers_normal
        )

        assert response.status_code == 200
        data = response.json()
        # Empty diff means no changes
        assert data["diff"] == {}

    def test_diff_nonexistent_version(self, client, normal_user, auth_headers_normal, db_session):
        """Test diff fails when version doesn't exist."""
        v1 = ConfigVersion(service_name="app", version=1, config={}, user_id=normal_user.id)
        db_session.add(v1)
        db_session.commit()

        response = client.get(
            f"/config/diff/app?version1_id={v1.id}&version2_id=99999",
            headers=auth_headers_normal
        )

        assert response.status_code == 404


class TestVersionIsolation:
    """Tests to ensure version isolation between users."""

    def test_user_cannot_see_other_user_versions(self, client, normal_user, admin_user, auth_headers_normal,
                                                 db_session):
        """Test that users only see their own versions."""
        # Create versions for both users
        v_user = ConfigVersion(service_name="shared", version=1, config={"owner": "user"}, user_id=normal_user.id)
        v_admin = ConfigVersion(service_name="shared", version=1, config={"owner": "admin"}, user_id=admin_user.id)
        db_session.add_all([v_user, v_admin])
        db_session.commit()

        response = client.get(
            "/config/versions/shared",
            headers=auth_headers_normal
        )

        data = response.json()
        assert len(data["versions"]) == 1
        assert data["versions"][0]["config"]["owner"] == "user"

    def test_user_cannot_rollback_other_user_version(self, client, normal_user, admin_user, auth_headers_normal,
                                                     db_session):
        """Test that users cannot roll back to another user's version."""
        # User's config
        user_config = ServiceConfig(name="app", config={"v": 2}, user_id=normal_user.id)
        db_session.add(user_config)

        # Admin's version (different user)
        admin_version = ConfigVersion(
            service_name="app",
            version=1,
            config={"malicious": "data"},
            user_id=admin_user.id
        )
        db_session.add(admin_version)
        db_session.commit()

        # Try to roll back to admin's version
        response = client.post(
            f"/config/rollback/app?target_version_id={admin_version.id}",
            headers=auth_headers_normal
        )

        # Should fail because version doesn't belong to user
        assert response.status_code == 404