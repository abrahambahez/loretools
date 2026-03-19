import scholartools.mcp_server as mcp_server


def test_module_imports():
    assert mcp_server is not None


def test_main_is_callable():
    assert callable(mcp_server.main)


def test_mcp_instance_exists():
    assert mcp_server.mcp is not None
