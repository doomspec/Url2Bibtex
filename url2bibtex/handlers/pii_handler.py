"""PII (Publisher Item Identifier) URL handler for BibTeX conversion."""

import re
from typing import Optional
import requests
from ..handler import Handler
from .doi_handler import DOIHandler


class PIIHandler(Handler):
    """
    Handler for ScienceDirect URLs containing PII (Publisher Item Identifier).

    Supports URLs like:
    - https://www.sciencedirect.com/science/article/pii/S1367593121001204
    - https://www.sciencedirect.com/science/article/abs/pii/S1367593121001204

    Will:
    1. Extract the PII from the URL
    2. Query CrossRef API to find the corresponding DOI
    3. Use DOI handler to fetch BibTeX
    """

    # CrossRef API endpoint
    CROSSREF_API = "https://api.crossref.org/works"

    # Pattern to match ScienceDirect PII URLs
    PII_PATTERN = re.compile(
        r"sciencedirect\.com/science/article/(?:abs/)?pii/([A-Z0-9]+)"
    )

    def __init__(self):
        """Initialize PII handler with DOI handler for BibTeX fetching."""
        super().__init__()
        self.doi_handler = DOIHandler()

    def can_handle(self, url: str) -> bool:
        """Check if this is a ScienceDirect PII URL."""
        return self.PII_PATTERN.search(url) is not None

    def extract_bibtex(self, url: str) -> Optional[str]:
        """Extract BibTeX entry from ScienceDirect PII URL."""
        # Extract PII from URL
        match = self.PII_PATTERN.search(url)
        if not match:
            return None

        pii = match.group(1)

        # Query CrossRef API to find DOI
        doi = self._get_doi_from_pii(pii)
        if not doi:
            return None

        # Use DOI handler to fetch BibTeX
        doi_url = f"https://doi.org/{doi}"
        bibtex = self.doi_handler.extract_bibtex(doi_url)

        return bibtex

    def _get_doi_from_pii(self, pii: str) -> Optional[str]:
        """
        Query CrossRef API to find DOI from PII.

        Args:
            pii: Publisher Item Identifier

        Returns:
            DOI string if found, None otherwise
        """
        try:
            # Query CrossRef API
            response = requests.get(
                self.CROSSREF_API,
                params={"query": pii},
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            # Check if we got results
            if data.get('message', {}).get('items'):
                # Return the DOI of the first result
                doi = data['message']['items'][0].get('DOI')
                return doi

        except requests.RequestException as e:
            print(f"Error querying CrossRef API: {e}")

        return None
