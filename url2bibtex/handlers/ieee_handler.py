"""IEEE Xplore URL handler for BibTeX conversion."""

import re
from typing import Optional
from ..handler import Handler
from ..utils import fetch_with_retry
from .doi_handler import DOIHandler


class IEEEHandler(Handler):
    """
    Handler for IEEE Xplore URLs.

    Supports URLs like:
    - https://ieeexplore.ieee.org/document/5288526
    - https://ieeexplore.ieee.org/abstract/document/5288526
    - http://ieeexplore.ieee.org/document/5288526/

    Extracts DOI link from the page and uses DOI handler to fetch BibTeX data.
    """

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

        # Fetch the HTML page to extract DOI link
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

        # Extract DOI link from the HTML
        doi_url = self._extract_doi_link(html_content)

        if not doi_url:
            print(f"Could not extract DOI link from IEEE document {doc_id}")
            return None

        # Use DOI handler to fetch BibTeX
        doi_handler = DOIHandler()
        bibtex = doi_handler.extract_bibtex(doi_url)

        return bibtex

    def _extract_doi_link(self, html_content: str) -> Optional[str]:
        """
        Extract DOI link from IEEE Xplore HTML page.

        Args:
            html_content: The HTML content of the IEEE page

        Returns:
            DOI URL string (e.g., "https://doi.org/10.1109/TPAMI.2024.3370978") or None if not found
        """
        # Pattern to match DOI links in the format: https://doi.org/10.xxxx/xxxxx
        doi_link_pattern = re.compile(r'https?://doi\.org/10\.\d+/[^\s\'"<>]+')
        match = doi_link_pattern.search(html_content)
        if match:
            return match.group(0)

        # If direct link not found, try to construct it from DOI value
        # Pattern 1: meta tag with DOI
        meta_pattern = re.compile(r'<meta[^>]+name="citation_doi"[^>]+content="([^"]+)"', re.IGNORECASE)
        match = meta_pattern.search(html_content)
        if match:
            doi = match.group(1)
            return f"https://doi.org/{doi}"

        # Pattern 2: DOI in JSON format
        doi_text_pattern = re.compile(r'"doi"\s*:\s*"(10\.\d+/[^"]+)"')
        match = doi_text_pattern.search(html_content)
        if match:
            doi = match.group(1)
            return f"https://doi.org/{doi}"

        # Pattern 3: xplore-pub-doi field
        xplore_doi_pattern = re.compile(r'"xplore-pub-doi"\s*:\s*"(10\.\d+/[^"]+)"')
        match = xplore_doi_pattern.search(html_content)
        if match:
            doi = match.group(1)
            return f"https://doi.org/{doi}"

        return None
