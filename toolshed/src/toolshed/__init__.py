import argparse
from .server import mcp

def main():
    """ToolShed MCP Server."""
    parser = argparse.ArgumentParser(
        description="ToolShed MCP Server for common Goose tools."
    )

    _ = parser.parse_args()
    mcp.run()


if __name__ == "__main__":
    main()
