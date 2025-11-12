"""IEEE Xplore URL handler for BibTeX conversion."""

import re
from typing import Optional
from ..handler import Handler
from ..utils import fetch_with_retry


class IEEEHandler(Handler):
    """
    Handler for IEEE Xplore URLs.

    Supports URLs like:
    - https://ieeexplore.ieee.org/document/5288526
    - https://ieeexplore.ieee.org/abstract/document/5288526
    - http://ieeexplore.ieee.org/document/5288526/

    Uses DOI resolution via doi.org to fetch BibTeX data.
    """

    # DOI resolution endpoint
    DOI_API = "https://doi.org"

    # Pattern to match IEEE Xplore URLs and extract the document ID
    IEEE_PATTERN = re.compile(
        r"ieeexplore\.ieee\.org/(?:document|abstract/document)/(\d+)"
    )

    def can_handle(self, url: str) -> bool:
        """Check if this is an IEEE Xplore URL."""
        return self.IEEE_PATTERN.search(url) is not None

    def extract_bibtex(self, url: str) -> Optional[str]:
        """Extract BibTeX entry from IEEE Xplore URL."""
        # Extract document ID from URL
        match = self.IEEE_PATTERN.search(url)
        if not match:
            return None

        doc_id = match.group(1)

        # Fetch the HTML page to extract DOI
        content = fetch_with_retry(
            url,
            accept_header='text/html',
            use_browser_headers=True
        )

        if not content:
            return None

        # Decode content if it's bytes
        if isinstance(content, bytes):
            html_content = content.decode('utf-8', errors='ignore')
        else:
            html_content = content

        # Try to extract DOI from the page
        # IEEE pages typically have DOI in meta tags or in the page content
        doi = self._extract_doi(html_content)

        if not doi:
            print(f"Could not extract DOI from IEEE document {doc_id}")
            return None

        # Fetch BibTeX from DOI.org using content negotiation
        bibtex = fetch_with_retry(
            f"{self.DOI_API}/{doi}",
            accept_header='application/x-bibtex',
            use_browser_headers=False
        )

        if not bibtex:
            return None

        # The response is already in BibTeX format (bytes)
        if isinstance(bibtex, bytes):
            bibtex = bibtex.decode('utf-8')

        # Clean up the BibTeX (sometimes has extra whitespace)
        bibtex = bibtex.strip()

        return bibtex if bibtex else None

    def _extract_doi(self, html_content: str) -> Optional[str]:
        """
        Extract DOI from IEEE Xplore HTML page.

        Args:
            html_content: The HTML content of the IEEE page

        Returns:
            DOI string or None if not found
        """
        # Try multiple patterns to find DOI

        # Pattern 1: meta tag with DOI
        meta_pattern = re.compile(r'<meta[^>]+name="citation_doi"[^>]+content="([^"]+)"', re.IGNORECASE)
        match = meta_pattern.search(html_content)
        if match:
            return match.group(1)

        # Pattern 2: Direct DOI link
        doi_link_pattern = re.compile(r'https?://doi\.org/(10\.\d+/[^\s\'"<>]+)')
        match = doi_link_pattern.search(html_content)
        if match:
            return match.group(1)

        # Pattern 3: DOI in text format
        doi_text_pattern = re.compile(r'"doi"\s*:\s*"(10\.\d+/[^"]+)"')
        match = doi_text_pattern.search(html_content)
        if match:
            return match.group(1)

        # Pattern 4: xploreDocumentDOI or similar fields
        xplore_doi_pattern = re.compile(r'"xplore-pub-doi"\s*:\s*"(10\.\d+/[^"]+)"')
        match = xplore_doi_pattern.search(html_content)
        if match:
            return match.group(1)

        return None
