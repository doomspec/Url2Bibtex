"""
MCP server for the url2bibtex tool.

Exposes url2bibtex functionality as an MCP tool that can be called by Claude and other AI assistants.
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from url2bibtex.default_converter import default_converter


# Create the MCP server
app = Server("url2bibtex")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="convert_url_to_bibtex",
            description=(
                "Convert a URL to a paper or article into a BibTeX citation entry. "
                "Supports various sources including arXiv, DOI, IEEE, OpenReview, "
                "Semantic Scholar, GitHub repositories, ACL Anthology, BioRxiv, "
                "Cell Press, PII, and more. Also supports direct BibTeX URLs with bib= parameter."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to convert to BibTeX (e.g., arxiv.org/abs/..., doi.org/..., ieeexplore.ieee.org/...)"
                    }
                },
                "required": ["url"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name != "convert_url_to_bibtex":
        raise ValueError(f"Unknown tool: {name}")

    url = arguments.get("url")
    if not url:
        raise ValueError("url is required")

    try:
        # Check if the URL can be converted
        if not default_converter.can_convert(url):
            raise ValueError(
                f"Unable to convert URL: {url}\n\n"
                "This URL is not supported by any registered handler. "
                "Supported sources include: arXiv, DOI, IEEE, OpenReview, "
                "Semantic Scholar, GitHub, ACL Anthology, BioRxiv, Cell Press, PII, and more."
            )

        # Convert the URL to BibTeX
        bibtex = default_converter.convert(url)

        if not bibtex:
            raise ValueError(f"Failed to extract BibTeX from URL: {url}")

        return [TextContent(type="text", text=bibtex)]

    except Exception as e:
        raise ValueError(f"Error converting URL to BibTeX: {e}")


async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def run():
    """Synchronous entry point for the server."""
    import asyncio
    asyncio.run(main())


if __name__ == "__main__":
    run()
