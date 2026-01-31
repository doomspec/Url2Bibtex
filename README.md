# url2bibtex

Convert paper URLs to BibTeX entries with a pluggable handler system.

## Features

- **Pluggable Handler System**: Easy to extend with custom handlers for different URL types
- **ArXiv Support**: Built-in handler for arXiv papers
- **OpenReview Support**: Built-in handler for OpenReview papers
- **Semantic Scholar Support**: Built-in handler for Semantic Scholar papers
- **GitHub Support**: Built-in handler for GitHub repositories (with CITATION.cff support)
- **DOI Support**: Built-in handler for DOI links (using DOI.org content negotiation)
- **HTML Meta Tags Fallback**: Universal fallback handler that extracts from HTML meta tags (citation_*, DC.*, og:*)
- **Simple API**: Clean and intuitive interface
- **Type-Safe**: Full type hints support

## Installation

### Using pip

```bash
pip install -e .
```

To use the MCP server:

```bash
pip install -e ".[mcp]"
```

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and runner:

```bash
# Install dependencies
uv sync

# Install with MCP support
uv sync --extra mcp
```

## Quick Start

```python
from url2bibtex import Url2Bibtex
from url2bibtex.handlers import (
    ArxivHandler, OpenReviewHandler, SemanticScholarHandler,
    GitHubHandler, DOIHandler, HTMLMetaHandler
)

# Create converter instance
converter = Url2Bibtex()

# Register specific handlers first
converter.register_handler(ArxivHandler())
converter.register_handler(OpenReviewHandler())
converter.register_handler(SemanticScholarHandler())
converter.register_handler(GitHubHandler())
converter.register_handler(DOIHandler())

# Register HTMLMetaHandler LAST as fallback for any other URLs
converter.register_handler(HTMLMetaHandler())

# Convert ArXiv URL to BibTeX
arxiv_url = "https://arxiv.org/abs/2103.15348"
bibtex = converter.convert(arxiv_url)
print(bibtex)

# Convert DOI to BibTeX
doi_url = "https://doi.org/10.1038/nature12373"
bibtex = converter.convert(doi_url)
print(bibtex)

# The fallback handler works with any publisher that has meta tags
publisher_url = "https://www.nature.com/articles/nature12373"
bibtex = converter.convert(publisher_url)
print(bibtex)
```

## MCP Server

url2bibtex includes an MCP (Model Context Protocol) server that allows Claude and other AI assistants to convert URLs to BibTeX entries.

**🚀 [Quick Start Guide](QUICKSTART_MCP.md)** | **📖 [Detailed Setup](MCP_SETUP.md)**

### Running the Server

After installing with MCP dependencies:

#### Using uv (Recommended)

```bash
uv run url2bibtex-server
```

Or from the project directory:

```bash
cd /path/to/Url2Bibtex
uv run url2bibtex-server
```

#### Using Python directly

```bash
url2bibtex-server
```

Or:

```bash
python -m url2bibtex.server
```

### Configuration

#### Automatic Installation (Easiest)

Install the configuration automatically:

```bash
python install_mcp_config.py
```

This will find your Claude config file and add the url2bibtex server automatically.

#### Generate Config for Manual Setup

Generate the config with the correct path:

```bash
python generate_mcp_config.py
```

Then copy the output to your Claude MCP settings file (`~/.claude/claude_desktop_config.json`).

#### Manual Configuration

Add to your Claude Code MCP settings file:

**Using uv (Recommended):**

```json
{
  "mcpServers": {
    "url2bibtex": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/Url2Bibtex",
        "run",
        "url2bibtex-server"
      ]
    }
  }
}
```

Replace `/path/to/Url2Bibtex` with the actual path to your url2bibtex project directory.

#### Using installed package

If you've installed url2bibtex globally:

```json
{
  "mcpServers": {
    "url2bibtex": {
      "command": "url2bibtex-server"
    }
  }
}
```

#### Using Python directly

```json
{
  "mcpServers": {
    "url2bibtex": {
      "command": "python",
      "args": ["-m", "url2bibtex.server"]
    }
  }
}
```

### Using the MCP Tool

Once configured, Claude can convert URLs to BibTeX entries:

```
User: Convert this URL to BibTeX: https://arxiv.org/abs/2103.15348
Claude: [Uses the convert_url_to_bibtex tool to get the BibTeX entry]
```

The MCP server includes a pre-configured converter with all built-in handlers registered in the optimal order.

## Creating Custom Handlers

You can easily create custom handlers for different types of URLs:

```python
from url2bibtex import Handler
import re
import requests

class MyCustomHandler(Handler):
    """Handler for custom paper repository."""

    def can_handle(self, url: str) -> bool:
        """Check if this handler can process the URL."""
        return "mycustomsite.com" in url

    def extract_bibtex(self, url: str) -> str:
        """Extract BibTeX from the URL."""
        # Your implementation here
        # 1. Request the URL
        # 2. Parse metadata
        # 3. Format as BibTeX
        response = requests.get(url)
        # ... process response ...
        return bibtex_string

# Register your custom handler
converter.register_handler(MyCustomHandler())
```

## Supported Platforms

Currently supported:
- **arXiv**: `https://arxiv.org/abs/XXXX.XXXXX`
- **OpenReview**: `https://openreview.net/forum?id=PAPER_ID`
- **Semantic Scholar**: `https://www.semanticscholar.org/paper/{title-slug}/{paper-id}`
- **GitHub**: `https://github.com/{owner}/{repo}` (supports CITATION.cff)
- **DOI**: `https://doi.org/10.XXXX/XXXXX` (works with any DOI-registered publication)
- **HTML Meta Tags**: Any website with citation meta tags (Nature, IEEE, ACM, Springer, etc.)

## Universal Fallback Handler

The `HTMLMetaHandler` is a universal fallback that extracts BibTeX information from HTML meta tags. It supports:

- **citation_*** tags (Google Scholar format) - used by most academic publishers
- **DC.*** tags (Dublin Core metadata)
- **og:*** tags (Open Graph protocol)

**Important**: Register `HTMLMetaHandler` LAST, after all specific handlers, as it matches any HTTP(S) URL.

### Supported Publishers

The fallback handler works with any website that includes citation metadata in HTML:
- Nature, Science, Cell Press
- IEEE Xplore, ACM Digital Library
- Springer, Elsevier, Wiley
- PLOS, MDPI, Frontiers
- And many more...

## Architecture

The package is built around three core components:

1. **Handler**: Abstract base class that defines the interface for URL handlers
2. **HandlerRegistry**: Manages registered handlers and routes URLs to appropriate handlers
3. **Url2Bibtex**: Main converter class that provides the public API

### Handler Interface

```python
class Handler(ABC):
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Check if this handler can process the URL."""
        pass

    @abstractmethod
    def extract_bibtex(self, url: str) -> Optional[str]:
        """Extract BibTeX entry from the URL."""
        pass
```

## Example Output

For arXiv URL `https://arxiv.org/abs/2103.15348`:

```bibtex
@article{wang2021,
  title = {Training Data Efficient Image Transformers & Distillation through Attention},
  author = {Hugo Touvron and Matthieu Cord and Matthijs Douze and Francisco Massa and Alexandre Sablayrolles and Hervé Jégou},
  year = {2021},
  journal = {arXiv preprint arXiv:2103.15348},
  eprint = {2103.15348},
  archivePrefix = {arXiv},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2103.15348}
}
```

## License

MIT License

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.
