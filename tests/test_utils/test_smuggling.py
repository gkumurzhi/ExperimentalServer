"""Direct tests for the HTML smuggling renderer contract."""

from src.utils.smuggling import generate_smuggling_html


def test_generate_smuggling_html_plain_output_escapes_filename() -> None:
    html = generate_smuggling_html(
        file_data=b"hello world",
        filename='report "quoted".txt',
    )

    assert "Downloading..." in html
    assert 'var fn="report \\"quoted\\".txt";' in html
    assert "Done! File: " in html
    assert "Protected File" not in html


def test_generate_smuggling_html_encrypted_default_script_path_and_captcha() -> None:
    html = generate_smuggling_html(
        file_data=b"secret payload",
        filename="secret.txt",
        password="hunter2",
        password_captcha="data:image/png;base64,AAAA",
    )

    assert "Protected File" in html
    assert 'src="data:image/png;base64,AAAA"' in html
    assert '<script src="/static/crypto-js.min.js"></script>' in html
    assert "Downloaded: " in html


def test_generate_smuggling_html_honors_custom_crypto_js_src() -> None:
    html = generate_smuggling_html(
        file_data=b"secret payload",
        filename="secret.txt",
        password="hunter2",
        crypto_js_src="/static/vendor/crypto-js.min.js?v=2",
    )

    assert '<script src="/static/vendor/crypto-js.min.js?v=2"></script>' in html
    assert '<script src="/static/crypto-js.min.js"></script>' not in html
