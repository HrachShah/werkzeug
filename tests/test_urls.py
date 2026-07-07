import pytest

from werkzeug import urls


def test_iri_support():
    assert urls.uri_to_iri("http://xn--n3h.net/") == "http://\u2603.net/"
    assert urls.iri_to_uri("http://☃.net/") == "http://xn--n3h.net/"
    assert (
        urls.iri_to_uri("http://üser:pässword@☃.net/påth")
        == "http://%C3%BCser:p%C3%A4ssword@xn--n3h.net/p%C3%A5th"
    )
    assert (
        urls.uri_to_iri("http://test.com/%3Fmeh?foo=%26%2F")
        == "http://test.com/%3Fmeh?foo=%26/"
    )
    assert urls.iri_to_uri("/foo") == "/foo"
    assert (
        urls.iri_to_uri("http://föö.com:8080/bam/baz")
        == "http://xn--f-1gaa.com:8080/bam/baz"
    )


def test_iri_safe_quoting():
    uri = "http://xn--f-1gaa.com/%2F%25?q=%C3%B6&x=%3D%25#%25"
    iri = "http://föö.com/%2F%25?q=ö&x=%3D%25#%25"
    assert urls.uri_to_iri(uri) == iri
    assert urls.iri_to_uri(urls.uri_to_iri(uri)) == uri


def test_quoting_of_local_urls():
    rv = urls.iri_to_uri("/foo\x8f")
    assert rv == "/foo%C2%8F"


def test_iri_to_uri_idempotence_ascii_only():
    uri = "http://www.idempoten.ce"
    uri = urls.iri_to_uri(uri)
    assert urls.iri_to_uri(uri) == uri


def test_iri_to_uri_idempotence_non_ascii():
    uri = "http://\N{SNOWMAN}/\N{SNOWMAN}"
    uri = urls.iri_to_uri(uri)
    assert urls.iri_to_uri(uri) == uri


def test_uri_to_iri_idempotence_ascii_only():
    uri = "http://www.idempoten.ce"
    uri = urls.uri_to_iri(uri)
    assert urls.uri_to_iri(uri) == uri


def test_uri_to_iri_idempotence_non_ascii():
    uri = "http://xn--n3h/%E2%98%83"
    uri = urls.uri_to_iri(uri)
    assert urls.uri_to_iri(uri) == uri


def test_iri_to_uri_to_iri():
    iri = "http://föö.com/"
    uri = urls.iri_to_uri(iri)
    assert urls.uri_to_iri(uri) == iri


def test_uri_to_iri_to_uri():
    uri = "http://xn--f-rgao.com/%C3%9E"
    iri = urls.uri_to_iri(uri)
    assert urls.iri_to_uri(iri) == uri


@pytest.mark.parametrize(
    "value",
    [
        "http://föñ.com/\N{BALLOT BOX}/fred?utf8=\u2713",
        "http://xn--f-rgao.com/\u2610/fred?utf8=\N{CHECK MARK}",
        "http://xn--f-rgao.com/%E2%98%90/fred?utf8=%E2%9C%93",
        "http://xn--f-rgao.com/%E2%98%90/fred?utf8=%E2%9C%93",
        "http://föñ.com/\u2610/fred?utf8=%E2%9C%93",
    ],
)
def test_uri_iri_normalization(value):
    uri = "http://xn--f-rgao.com/%E2%98%90/fred?utf8=%E2%9C%93"
    iri = "http://föñ.com/\N{BALLOT BOX}/fred?utf8=\u2713"
    assert urls.uri_to_iri(value) == iri
    assert urls.iri_to_uri(value) == uri
    assert urls.uri_to_iri(urls.iri_to_uri(value)) == iri
    assert urls.iri_to_uri(urls.uri_to_iri(value)) == uri
    assert urls.uri_to_iri(urls.uri_to_iri(value)) == iri
    assert urls.iri_to_uri(urls.iri_to_uri(value)) == uri


def test_uri_to_iri_dont_unquote_space():
    assert urls.uri_to_iri("abc%20def") == "abc%20def"


def test_iri_to_uri_dont_quote_valid_code_points():
    # [] are not valid URL code points according to WhatWG URL Standard
    # https://url.spec.whatwg.org/#url-code-points
    assert urls.iri_to_uri("/path[bracket]?(paren)") == "/path%5Bbracket%5D?(paren)"


# Python < 3.12
def test_itms_services() -> None:
    url = "itms-services://?action=download-manifest&url=https://test.example/path"
    assert urls.iri_to_uri(url) == url


@pytest.mark.parametrize(
    ("uri", "expected_uri"),
    [
        # Empty username, non-empty password: present-but-empty username must survive.
        ("http://:pass@example.com/path", "http://:pass@example.com/path"),
        # Non-empty username, empty password: present-but-empty password must survive.
        ("http://user:@example.com/path", "http://user:@example.com/path"),
        # Both empty.
        ("http://:@example.com/path", "http://:@example.com/path"),
        # Username only, no password at all (None, not empty): no separator.
        ("http://user@example.com/path", "http://user@example.com/path"),
        # No userinfo at all.
        ("http://example.com/path", "http://example.com/path"),
    ],
)
def test_uri_to_iri_preserves_empty_userinfo(uri, expected_uri):
    """An empty-but-present username or password must round-trip, not be dropped.

    ``urllib.parse.urlsplit`` distinguishes a present-but-empty component
    (``""``) from a missing one (``None``); ``uri_to_iri`` / ``iri_to_uri``
    should preserve that distinction instead of treating an empty string as
    missing.
    """
    assert urls.uri_to_iri(uri) == expected_uri
    assert urls.iri_to_uri(uri) == expected_uri


def test_uri_to_iri_preserves_empty_userinfo_with_percent_encoded_password():
    """Percent-encoded bytes in an empty-username userinfo must round-trip.

    Pre-fix, the empty username is treated as missing, so the userinfo section
    is dropped entirely from the output. Post-fix, the userinfo is preserved.
    """
    out = urls.uri_to_iri("http://:p%40ss@example.com/path")
    assert out.startswith("http://:") and out.endswith("@example.com/path")
    out2 = urls.iri_to_uri("http://:p%40ss@example.com/path")
    assert out2.startswith("http://:") and out2.endswith("@example.com/path")
