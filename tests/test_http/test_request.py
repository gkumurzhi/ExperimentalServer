"""Tests for HTTP request parsing."""


from src.http.request import HTTPRequest


class TestHTTPRequest:
    """Tests for HTTPRequest class."""

    def test_parse_simple_get_request(self):
        """Test parsing a simple GET request."""
        raw = b"GET /index.html HTTP/1.1\r\nHost: localhost\r\n\r\n"
        request = HTTPRequest(raw)

        assert request.method == "GET"
        assert request.path == "/index.html"
        assert request.http_version == "HTTP/1.1"
        assert request.headers.get("host") == "localhost"

    def test_parse_post_request_with_body(self):
        """Test parsing a POST request with body."""
        raw = (
            b"POST /upload HTTP/1.1\r\n"
            b"Host: localhost\r\n"
            b"Content-Length: 13\r\n"
            b"Content-Type: text/plain\r\n"
            b"\r\n"
            b"Hello, World!"
        )
        request = HTTPRequest(raw)

        assert request.method == "POST"
        assert request.path == "/upload"
        assert request.content_length == 13
        assert request.body == b"Hello, World!"

    def test_parse_url_encoded_path(self):
        """Test parsing URL-encoded paths."""
        raw = b"GET /file%20with%20spaces.txt HTTP/1.1\r\nHost: localhost\r\n\r\n"
        request = HTTPRequest(raw)

        assert request.path == "/file with spaces.txt"

    def test_get_header_case_insensitive(self):
        """Test that header lookup is case-insensitive."""
        raw = b"GET / HTTP/1.1\r\nContent-Type: application/json\r\n\r\n"
        request = HTTPRequest(raw)

        assert request.get_header("content-type") == "application/json"
        assert request.get_header("Content-Type") == "application/json"
        assert request.get_header("CONTENT-TYPE") == "application/json"

    def test_get_header_with_default(self):
        """Test header lookup with default value."""
        raw = b"GET / HTTP/1.1\r\n\r\n"
        request = HTTPRequest(raw)

        assert request.get_header("x-custom", "default") == "default"

    def test_content_type_default(self):
        """Test default content type."""
        raw = b"GET / HTTP/1.1\r\n\r\n"
        request = HTTPRequest(raw)

        assert request.content_type == "application/octet-stream"

    def test_query_params_parsed(self):
        """Test query string parameters are parsed."""
        raw = b"GET /dir?offset=10&limit=50 HTTP/1.1\r\n\r\n"
        request = HTTPRequest(raw)

        assert request.path == "/dir"
        assert request.query_params["offset"] == "10"
        assert request.query_params["limit"] == "50"

    def test_query_params_empty(self):
        """Test missing query string yields empty dict."""
        raw = b"GET /plain HTTP/1.1\r\n\r\n"
        request = HTTPRequest(raw)

        assert request.query_params == {}

    def test_repr(self):
        """Test string representation."""
        raw = b"GET /test HTTP/1.1\r\n\r\n"
        request = HTTPRequest(raw)

        assert "GET" in repr(request)
        assert "/test" in repr(request)
