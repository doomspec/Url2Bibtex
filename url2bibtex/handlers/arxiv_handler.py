"""ArXiv URL handler for BibTeX conversion."""

import re
import xml.etree.ElementTree as ET
from typing import Optional
from ..handler import Handler
from ..utils import fetch_with_retry


class ArxivHandler(Handler):
    """
    Handler for ArXiv URLs.

    Supports URLs like:
    - https://arxiv.org/abs/2103.15348
    - https://arxiv.org/pdf/2103.15348.pdf
    - http://arxiv.org/abs/2103.15348v1
    - http://arxiv.org/html/2103.15348v1
    """

    # ArXiv API endpoint
    ARXIV_API = "http://export.arxiv.org/api/query"

    # Pattern to match arXiv URLs and extract the paper ID
    ARXIV_PATTERN = re.compile(
        r"arxiv\.org/(?:abs|pdf|html)/(\d+\.\d+)(?:v\d+)?(?:\.pdf)?"
    )

    def can_handle(self, url: str) -> bool:
        """Check if this is an arXiv URL."""
        return self.ARXIV_PATTERN.search(url) is not None

    def extract_bibtex(self, url: str) -> Optional[str]:
        """Extract BibTeX entry from arXiv URL."""
        # Extract arXiv ID from URL
        match = self.ARXIV_PATTERN.search(url)
        if not match:
            return None

        arxiv_id = match.group(1)

        # Fetch metadata from arXiv API with retry logic
        content = fetch_with_retry(
            self.ARXIV_API,
            {"id_list": arxiv_id},
            accept_header='application/atom+xml'
        )
        if not content:
            return None

        # Parse XML response
        try:
            root = ET.fromstring(content)
            # Define namespace
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }

            # Find the entry element
            entry = root.find('atom:entry', ns)
            if entry is None:
                return None

            # Extract metadata
            title = entry.find('atom:title', ns)
            title_text = title.text.strip().replace('\n', ' ') if title is not None else "Unknown Title"

            # Extract authors
            authors = entry.findall('atom:author', ns)
            author_list = []
            for author in authors:
                name_elem = author.find('atom:name', ns)
                if name_elem is not None:
                    author_list.append(name_elem.text)

            # Join authors with 'and'
            authors_str = ' and '.join(author_list)

            # Extract publication date (year)
            published = entry.find('atom:published', ns)
            year = published.text[:4] if published is not None else "Unknown"

            # Extract primary category for note field
            primary_category = entry.find('arxiv:primary_category', ns)
            category = primary_category.get('term') if primary_category is not None else ''

            # Generate BibTeX key (first author's last name + year)
            if author_list:
                first_author_last = author_list[0].split()[-1].lower()
                bibtex_key = f"{first_author_last}{year}"
            else:
                bibtex_key = f"arxiv{year}"

            # Construct BibTeX entry
            bibtex = f"""@article{{{bibtex_key},
  title = {{{title_text}}},
  author = {{{authors_str}}},
  year = {{{year}}},
  journal = {{arXiv preprint arXiv:{arxiv_id}}},
  eprint = {{{arxiv_id}}},
  archivePrefix = {{arXiv}},
  primaryClass = {{{category}}},
  url = {{https://arxiv.org/abs/{arxiv_id}}}
}}"""

            return bibtex

        except ET.ParseError as e:
            print(f"Error parsing arXiv XML response: {e}")
            return None
