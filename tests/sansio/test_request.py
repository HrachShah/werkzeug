import pytest

from werkzeug.datastructures import Headers
from werkzeug.http import SecFetchMode
from werkzeug.http import SecFetchSite
from werkzeug.sansio.request import Request


@pytest.mark.parametrize(
    "headers, expected",
    [
        (Headers({"Transfer-Encoding": "chunked", "Content-Length": "6"}), None),
        (Headers({"Transfer-Encoding": "something", "Content-Length": "6"}), 6),
        (Headers({"Content-Length": "6"}), 6),
        (Headers({"Content-Length": "-6"}), 0),
        (Headers({"Content-Length": "+123"}), 0),
        (Headers({"Content-Length": "1_23"}), 0),
        (Headers({"Content-Length": "🯱🯲🯳"}), 0),
        (Headers(), None),
    ],
)
def test_content_length(headers: Headers, expected: int | None) -> None:
    req = Request("POST", "http", None, "", "", b"", headers, None)
    assert req.content_length == expected


def test_cookies() -> None:
    headers = Headers([("Cookie", "a=b"), ("Content-Type", "text"), ("Cookie", "a=c")])
    req = Request("GET", "http", None, "", "", b"", headers, None)
    assert req.cookies.get("a") == "b"
    assert req.cookies.getlist("a") == ["b", "c"]


@pytest.mark.parametrize(
    "headers, expected",
    [
        (Headers([("Sec-Fetch-Mode", "cors")]), SecFetchMode.CORS),
        (Headers([("Sec-Fetch-Mode", "invalid")]), None),
        (Headers({}), None),
    ],
)
def test_sec_fetch_mode(headers: Headers, expected: SecFetchMode | None) -> None:
    req = Request("POST", "http", None, "", "", b"", headers, None)
    assert req.sec_fetch_mode == expected


@pytest.mark.parametrize(
    "headers, expected",
    [
        (Headers([("Sec-Fetch-Site", "cross-site")]), SecFetchSite.CROSS_SITE),
        (Headers([("Sec-Fetch-Site", "invalid")]), None),
        (Headers({}), None),
    ],
)
def test_sec_fetch_site(headers: Headers, expected: SecFetchSite | None) -> None:
    req = Request("POST", "http", None, "", "", b"", headers, None)
    assert req.sec_fetch_site == expected


def test_repr_idna_failure() -> None:
    # When the server's host is an IDNA label that fails to decode
    # (here: empty punycode "xn--"), uri_to_iri raises UnicodeError
    # ("label empty or too long"). __repr__ catches that and renders
    # the URL as "(invalid URL: ...)".
    req = Request(
        "GET", "http", ("xn--", 80), "", "/foo", b"", Headers(), None
    )
    assert repr(req) == "<Request '(invalid URL: label empty or too long)' [GET]>"


def test_repr_propagates_attributeerror() -> None:
    # If self.url raises something other than ValueError/TypeError/UnicodeError
    # (e.g. a programmer error inside the property chain), __repr__ should
    # let it propagate instead of swallowing it as "(invalid URL: ...)".
    class _BadHeaders:
        def get(self, *args, **kwargs):  # pragma: no cover - not called
            raise AssertionError("should not be called")

    class _BadRequest(Request):
        pass

    req = _BadRequest(
        "GET", "http", ("example.com", 80), "", "/", b"", _BadHeaders(), None
    )
    try:
        repr(req)
    except (ValueError, TypeError, UnicodeError) as e:
        pytest.fail(
            f"__repr__ swallowed {type(e).__name__}; it should propagate"
        )