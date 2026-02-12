"""Tests for HTTP response building."""

from pathlib import Path

from src.http.response import HTTPResponse


class TestHTTPResponse:
    """Tests for HTTPResponse class."""

    def test_default_status_code(self):
        """Test default status code is 200."""
        response = HTTPResponse()
        assert response.status_code == 200

    def test_custom_status_code(self):
        """Test setting custom status code."""
        response = HTTPResponse(404)
        assert response.status_code == 404

    def test_set_header(self):
        """Test setting headers."""
        response = HTTPResponse()
        response.set_header("X-Custom", "value")

        assert response.headers["X-Custom"] == "value"

    def test_set_body_string(self):
        """Test setting body as string."""
        response = HTTPResponse()
        response.set_body("Hello, World!", "text/plain")

        assert response.body == b"Hello, World!"
        assert response.headers["Content-Type"] == "text/plain"
        assert response.headers["Content-Length"] == "13"

    def test_set_body_bytes(self):
        """Test setting body as bytes."""
        response = HTTPResponse()
        response.set_body(b"\x00\x01\x02", "application/octet-stream")

        assert response.body == b"\x00\x01\x02"
        assert response.headers["Content-Length"] == "3"

    def test_build_response(self):
        """Test building complete HTTP response."""
        response = HTTPResponse(200)
        response.set_body("OK", "text/plain")
        built = response.build()

        assert built.startswith(b"HTTP/1.1 200 OK\r\n")
        assert b"Content-Type: text/plain\r\n" in built
        assert b"Content-Length: 2\r\n" in built
        assert built.endswith(b"\r\n\r\nOK")

    def test_build_opsec_mode(self):
        """Test building response in OPSEC mode."""
        response = HTTPResponse(200)
        response.set_body("OK", "text/plain")
        built = response.build(opsec_mode=True)

        assert b"Server: nginx\r\n" in built

    def test_build_normal_mode(self):
        """Test building response in normal mode."""
        response = HTTPResponse(200)
        response.set_body("OK", "text/plain")
        built = response.build(opsec_mode=False)

        assert b"Server: ExperimentalHTTPServer/2.0.0\r\n" in built

    def test_cors_headers(self):
        """Test CORS headers are included."""
        response = HTTPResponse(200)
        response.set_body("OK", "text/plain")
        built = response.build()

        assert b"Access-Control-Allow-Origin: *\r\n" in built

    def test_set_file_streaming(self, tmp_path: Path):
        """Test set_file sets stream_path and correct headers."""
        f = tmp_path / "data.bin"
        f.write_bytes(b"A" * 256)
        response = HTTPResponse(200)
        response.set_file(f, "application/octet-stream")

        assert response.stream_path == f
        assert response.body == b""  # body stays empty
        assert response.headers["Content-Length"] == "256"
        assert response.headers["Content-Type"] == "application/octet-stream"

    def test_build_headers_only(self):
        """Test build_headers returns header bytes without body."""
        response = HTTPResponse(200)
        response.set_body("hello", "text/plain")
        headers = response.build_headers()

        assert headers.startswith(b"HTTP/1.1 200 OK\r\n")
        assert headers.endswith(b"\r\n")
        assert b"hello" not in headers  # body excluded

    def test_connection_close_by_default(self):
        """Test that Connection: close is set by default."""
        response = HTTPResponse(200)
        response.set_body("OK", "text/plain")
        built = response.build()
        assert b"Connection: close\r\n" in built

    def test_keep_alive_headers(self):
        """Test keep-alive Connection and Keep-Alive headers."""
        response = HTTPResponse(200)
        response.set_body("OK", "text/plain")
        built = response.build(keep_alive=True, keep_alive_timeout=10, keep_alive_max=50)
        assert b"Connection: keep-alive\r\n" in built
        assert b"Keep-Alive: timeout=10, max=50\r\n" in built

    def test_keep_alive_false_no_keepalive_header(self):
        """Test that Keep-Alive header is absent when keep_alive=False."""
        response = HTTPResponse(200)
        response.set_body("OK", "text/plain")
        built = response.build(keep_alive=False)
        assert b"Connection: close\r\n" in built
        assert b"Keep-Alive:" not in built

    def test_repr(self):
        """Test string representation."""
        response = HTTPResponse(404)
        assert "404" in repr(response)
