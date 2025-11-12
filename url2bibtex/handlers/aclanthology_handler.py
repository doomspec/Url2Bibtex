"""ACL Anthology URL handler for BibTeX conversion."""

import re
from typing import Optional
from ..handler import Handler
from ..utils import fetch_with_retry


class ACLAnthologyHandler(Handler):
    """
    Handler for ACL Anthology URLs.

    Supports URLs like:
    - https://aclanthology.org/2024.findings-emnlp.746
    - https://aclanthology.org/N19-1423/
    - https://www.aclweb.org/anthology/P19-1001

    ACL Anthology provides direct BibTeX export by appending .bib to the URL.
    """

    # Pattern to match ACL Anthology URLs and extract the paper ID
    ACL_PATTERN = re.compile(
        r"(?:aclanthology\.org|aclweb\.org/anthology)/([A-Za-z0-9.-]+?)/?(?:\.bib)?$"
    )

    def can_handle(self, url: str) -> bool:
        """Check if this is an ACL Anthology URL."""
        return self.ACL_PATTERN.search(url) is not None

    def extract_bibtex(self, url: str) -> Optional[str]:
        """Extract BibTeX entry from ACL Anthology URL."""
        # Extract paper ID from URL
        match = self.ACL_PATTERN.search(url)
        if not match:
            return None

        paper_id = match.group(1)

        # ACL Anthology provides BibTeX export by appending .bib
        bibtex_url = f"https://aclanthology.org/{paper_id}.bib"

        # Fetch BibTeX content
        bibtex = fetch_with_retry(
            bibtex_url,
            accept_header='text/plain',
            use_browser_headers=True
        )

        if not bibtex:
            return None

        # Convert bytes to string if needed
        if isinstance(bibtex, bytes):
            try:
                bibtex = bibtex.decode('utf-8')
            except UnicodeDecodeError:
                bibtex = bibtex.decode('latin-1')

        # Clean up the BibTeX
        bibtex = bibtex.strip()

        # Validate it looks like BibTeX
        if bibtex and bibtex.startswith('@'):
            return bibtex

        return None
