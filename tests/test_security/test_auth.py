"""Tests for authentication functionality."""

import base64

import pytest

from src.security.auth import (
    BasicAuthenticator,
    generate_random_credentials,
    hash_password,
    parse_basic_auth,
    verify_password,
)


class TestParseBasicAuth:
    """Tests for parse_basic_auth function."""

    def test_parse_valid_basic_auth(self):
        """Test parsing valid Basic auth header."""
        credentials = base64.b64encode(b"user:password").decode()
        header = f"Basic {credentials}"

        result = parse_basic_auth(header)

        assert result == ("user", "password")

    def test_parse_password_with_colon(self):
        """Test parsing password containing colons."""
        credentials = base64.b64encode(b"user:pass:word:extra").decode()
        header = f"Basic {credentials}"

        result = parse_basic_auth(header)

        assert result == ("user", "pass:word:extra")

    def test_parse_empty_header(self):
        """Test parsing empty header."""
        assert parse_basic_auth("") is None
        assert parse_basic_auth(None) is None  # type: ignore[arg-type]

    def test_parse_invalid_scheme(self):
        """Test parsing non-Basic auth."""
        assert parse_basic_auth("Bearer token123") is None

    def test_parse_invalid_base64(self):
        """Test parsing invalid base64."""
        assert parse_basic_auth("Basic not-valid-base64!!!") is None

    def test_parse_missing_colon(self):
        """Test parsing credentials without colon."""
        credentials = base64.b64encode(b"userpassword").decode()
        header = f"Basic {credentials}"

        assert parse_basic_auth(header) is None


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_generates_different_salts(self):
        """Test that each hash has a unique salt."""
        hash1, salt1 = hash_password("password")
        hash2, salt2 = hash_password("password")

        assert salt1 != salt2
        assert hash1 != hash2

    def test_hash_password_with_provided_salt(self):
        """Test hashing with a provided salt."""
        hash1, salt1 = hash_password("password", "fixed_salt")
        hash2, salt2 = hash_password("password", "fixed_salt")

        assert salt1 == salt2 == "fixed_salt"
        assert hash1 == hash2

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        hashed, salt = hash_password("correct_password")

        assert verify_password("correct_password", hashed, salt) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        hashed, salt = hash_password("correct_password")

        assert verify_password("wrong_password", hashed, salt) is False


class TestBasicAuthenticator:
    """Tests for BasicAuthenticator class."""

    def test_authenticate_with_valid_credentials(self):
        """Test authentication with valid credentials."""
        auth = BasicAuthenticator(credentials={"admin": "secret"})
        header = "Basic " + base64.b64encode(b"admin:secret").decode()

        assert auth.authenticate(header) is True

    def test_authenticate_with_invalid_password(self):
        """Test authentication with wrong password."""
        auth = BasicAuthenticator(credentials={"admin": "secret"})
        header = "Basic " + base64.b64encode(b"admin:wrong").decode()

        assert auth.authenticate(header) is False

    def test_authenticate_with_unknown_user(self):
        """Test authentication with unknown user."""
        auth = BasicAuthenticator(credentials={"admin": "secret"})
        header = "Basic " + base64.b64encode(b"unknown:secret").decode()

        assert auth.authenticate(header) is False

    def test_authenticate_without_header(self):
        """Test authentication without header."""
        auth = BasicAuthenticator(credentials={"admin": "secret"})

        assert auth.authenticate(None) is False

    def test_add_user(self):
        """Test adding a user after initialization."""
        auth = BasicAuthenticator()
        auth.add_user("newuser", "newpass")
        header = "Basic " + base64.b64encode(b"newuser:newpass").decode()

        assert auth.authenticate(header) is True

    def test_remove_user(self):
        """Test removing a user."""
        auth = BasicAuthenticator(credentials={"admin": "secret"})
        auth.remove_user("admin")
        header = "Basic " + base64.b64encode(b"admin:secret").decode()

        assert auth.authenticate(header) is False

    def test_custom_callback(self):
        """Test authentication with custom callback."""
        def custom_auth(username: str, password: str) -> bool:
            return username == "custom" and password == "callback"

        auth = BasicAuthenticator(auth_callback=custom_auth)
        header = "Basic " + base64.b64encode(b"custom:callback").decode()

        assert auth.authenticate(header) is True

    def test_www_authenticate_header(self):
        """Test WWW-Authenticate header generation."""
        auth = BasicAuthenticator(realm="Test Realm")

        assert auth.get_www_authenticate_header() == 'Basic realm="Test Realm"'


class TestGenerateRandomCredentials:
    """Tests for random credentials generation."""

    def test_generates_unique_credentials(self):
        """Test that each call generates unique credentials."""
        cred1 = generate_random_credentials()
        cred2 = generate_random_credentials()

        assert cred1 != cred2

    def test_username_format(self):
        """Test username format."""
        username, _ = generate_random_credentials()

        assert username.startswith("user_")

    def test_password_is_non_empty(self):
        """Test password is generated."""
        _, password = generate_random_credentials()

        assert len(password) > 0
