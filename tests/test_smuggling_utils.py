"""Renderer tests for safe HTML smuggling builder helpers."""

from src.utils import smuggling


def test_safe_smuggle_allowlists_are_fixed() -> None:
    assert smuggling.SAFE_SMUGGLE_EXTENSIONS == ("txt", "bin", "dat", "zip", "pdf")
    assert smuggling.SAFE_SMUGGLE_PRESETS == ("direct", "card_manual", "card_auto")


def test_resolve_safe_smuggle_download_filename_uses_allowlisted_extension() -> None:
    filename = smuggling.resolve_safe_smuggle_download_filename(
        source_filename="report.bin",
        download_name="Quarterly-Report",
        download_ext="pdf",
    )

    assert filename == "Quarterly-Report.pdf"


def test_resolve_safe_smuggle_download_filename_falls_back_to_safe_extension() -> None:
    filename = smuggling.resolve_safe_smuggle_download_filename(
        source_filename="report.exe",
        download_name="Quarterly-Report",
        download_ext="exe",
    )

    assert filename == "Quarterly-Report.bin"


def test_resolve_safe_smuggle_download_filename_normalizes_unsafe_stem() -> None:
    filename = smuggling.resolve_safe_smuggle_download_filename(
        source_filename="report.bin",
        download_name="../Quarterly\nReport ",
        download_ext="pdf",
    )

    assert filename == "Quarterly-Report.pdf"


def test_generate_smuggling_html_card_auto_includes_notice_and_countdown() -> None:
    html = smuggling.generate_smuggling_html(
        b"payload",
        "report.bin",
        builder=smuggling.SafeSmuggleBuilderConfig(
            download_name="Quarterly-Report",
            download_ext="pdf",
            preset="card_auto",
            title="Quarterly Report",
            message="Internal lab test artifact",
            cta_label="Download test artifact",
            delay_ms=1200,
            show_notice=True,
        ),
    )

    assert "Quarterly-Report.pdf" in html
    assert "Internal lab test artifact" in html
    assert "Test artifact notice: internal lab-only page." in html
    assert 'id="smuggleCountdown"' in html
    assert "setTimeout(startDownload, 1200)" in html


def test_generate_smuggling_html_builder_text_is_escaped() -> None:
    html = smuggling.generate_smuggling_html(
        b"payload",
        "report.bin",
        builder=smuggling.SafeSmuggleBuilderConfig(
            preset="card_manual",
            title="<b>Quarterly</b>",
            message='Use "lab" <script>alert(1)</script>',
            cta_label="Download <now>",
        ),
    )

    assert "&lt;b&gt;Quarterly&lt;/b&gt;" in html
    assert "Use &quot;lab&quot; &lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "Download &lt;now&gt;" in html
    assert "<b>Quarterly</b>" not in html
    assert "<script>alert(1)</script>" not in html


def test_generate_smuggling_html_without_builder_keeps_legacy_plain_renderer() -> None:
    html = smuggling.generate_smuggling_html(
        file_data=b"hello world",
        filename='report "quoted".txt',
    )

    assert "Downloading..." in html
    assert 'var fn="report \\"quoted\\".txt";' in html
    assert "setTimeout(d,500);" in html
    assert "Test artifact" not in html


def test_generate_smuggling_html_without_builder_preserves_original_filename() -> None:
    html = smuggling.generate_smuggling_html(
        file_data=b"hello world",
        filename="Report.EXE",
    )

    assert 'var fn="Report.EXE";' in html


def test_generate_smuggling_html_encrypted_builder_uses_resolved_filename() -> None:
    html = smuggling.generate_smuggling_html(
        file_data=b"secret payload",
        filename="report.bin",
        password="hunter2",
        builder=smuggling.SafeSmuggleBuilderConfig(
            download_name="Quarterly-Report",
            download_ext="pdf",
            preset="direct",
        ),
    )

    assert 'var fn="Quarterly-Report.pdf";' in html
    assert "CryptoJS.SHA256" in html
    assert '<script src="/static/crypto-js.min.js"></script>' in html


def test_generate_smuggling_html_builder_download_name_is_script_safe() -> None:
    html = smuggling.generate_smuggling_html(
        file_data=b"payload",
        filename="report.bin",
        builder=smuggling.SafeSmuggleBuilderConfig(
            download_name='</script><script>alert(1)</script>',
            download_ext="pdf",
            preset="direct",
        ),
    )

    assert "var fn=" in html
    assert 'var fn="</script>' not in html


def test_generate_smuggling_html_encrypted_builder_download_name_is_script_safe() -> None:
    html = smuggling.generate_smuggling_html(
        file_data=b"payload",
        filename="report.bin",
        password="hunter2",
        builder=smuggling.SafeSmuggleBuilderConfig(
            download_name='</script><script>alert(1)</script>',
            download_ext="pdf",
            preset="direct",
        ),
    )

    assert "var fn=" in html
    assert 'var fn="</script>' not in html
