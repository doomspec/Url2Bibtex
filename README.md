# url2bibtex

Convert paper URLs to BibTeX entries with a pluggable handler system.

## Features

- **Pluggable Handler System**: Easy to extend with custom handlers for different URL types
- **ArXiv Support**: Built-in handler for arXiv papers
- **OpenReview Support**: Built-in handler for OpenReview papers
- **Semantic Scholar Support**: Built-in handler for Semantic Scholar papers
- **GitHub Support**: Built-in handler for GitHub repositories (with CITATION.cff support)
- **DOI Support**: Built-in handler for DOI links (using DOI.org content negotiation)
- **Simple API**: Clean and intuitive interface
- **Type-Safe**: Full type hints support

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from url2bibtex import Url2Bibtex
from url2bibtex.handlers import ArxivHandler, OpenReviewHandler, SemanticScholarHandler, GitHubHandler, DOIHandler

# Create converter instance
converter = Url2Bibtex()

# Register handlers
converter.register_handler(ArxivHandler())
converter.register_handler(OpenReviewHandler())
converter.register_handler(SemanticScholarHandler())
converter.register_handler(GitHubHandler())
converter.register_handler(DOIHandler())

# Convert ArXiv URL to BibTeX
arxiv_url = "https://arxiv.org/abs/2103.15348"
bibtex = converter.convert(arxiv_url)
print(bibtex)

# Convert DOI to BibTeX
doi_url = "https://doi.org/10.1038/nature12373"
bibtex = converter.convert(doi_url)
print(bibtex)

# Convert GitHub repository to BibTeX
github_url = "https://github.com/pytorch/pytorch"
bibtex = converter.convert(github_url)
print(bibtex)
```

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
