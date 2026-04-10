from unittest.mock import patch


from ntfy_lite.actions import Action, HttpAction, HttpMethod, ViewAction


def test_action_init(mock_validators):
    """Test Action base class initialization."""
    with patch("validators.url") as mock_url:
        mock_url.return_value = True

        # Test with clear=False (default)
        action = Action("test_action", "Test Label", "https://example.com")
        assert action.action == "test_action"
        assert action.label == "Test Label"
        assert action.url == "https://example.com"
        assert action.clear is False

        # Test with clear=True
        action_clear = Action(
            "test_action", "Test Label", "https://example.com", clear=True
        )
        assert action_clear.clear is True

        # Test URL validation call
        mock_url.assert_called_with("https://example.com")


def test_action_str_helper():
    """Test Action._str helper method."""
    action = Action("test_action", "Test Label", "https://example.com", clear=False)
    attrs = ("label", "url", "clear")
    result = action._str(attrs)
    assert (
        result == "test_action, label=Test Label, url=https://example.com, clear=false"
    )

    # Test with some None values (should be skipped)
    action.test_attr = None
    result_with_none = action._str(("label", "test_attr"))
    assert result_with_none == "test_action, label=Test Label"


def test_view_action_init():
    """Test ViewAction initialization."""
    action = ViewAction("View Website", "https://is.mpg.de", clear=True)
    assert action.action == "view"
    assert action.label == "View Website"
    assert action.url == "https://is.mpg.de"
    assert action.clear is True


def test_view_action_str():
    """Test ViewAction __str__ method."""
    action = ViewAction("View Website", "https://is.mpg.de")
    assert str(action) == "view, label=View Website, url=https://is.mpg.de, clear=false"


def test_http_action_init():
    """Test HttpAction initialization."""
    headers = {"Authorization": "Bearer token"}
    body = '{"key": "value"}'
    action = HttpAction(
        "Post Data",
        "https://api.example.com",
        method=HttpMethod.POST,
        headers=headers,
        body=body,
    )
    assert action.action == "http"
    assert action.label == "Post Data"
    assert action.url == "https://api.example.com"
    assert action.method == HttpMethod.POST.value
    assert action.headers == headers
    assert action.body == body


def test_http_action_str():
    """Test HttpAction __str__ method."""
    # Test without headers
    action_no_headers = HttpAction(
        "Get Data", "https://api.example.com", method=HttpMethod.GET
    )
    expected_no_headers = (
        "http, label=Get Data, url=https://api.example.com, clear=false, method=1"
    )
    assert str(action_no_headers) == expected_no_headers

    # Test with headers
    headers = {"X-Custom": "Value", "Content-Type": "application/json"}
    action_with_headers = HttpAction(
        "Post Data",
        "https://api.example.com",
        method=HttpMethod.POST,
        headers=headers,
    )
    res = str(action_with_headers)
    assert (
        "http, label=Post Data, url=https://api.example.com, clear=false, method=2"
        in res
    )
    assert "headers.X-Custom=Value" in res
    assert "headers.Content-Type=application/json" in res
