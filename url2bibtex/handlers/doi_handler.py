"""DOI URL handler for BibTeX conversion."""

import re
from typing import Optional
from ..handler import Handler
from ..utils import fetch_with_retry


class DOIHandler(Handler):
    """
    Handler for DOI URLs.

    Supports URLs like:
    - https://doi.org/10.1000/xyz123
    - http://dx.doi.org/10.1000/xyz123
    - doi:10.1000/xyz123
    - https://pubs.acs.org/doi/10.1021/acs.chemrestox.5c00033
    - https://journals.sagepub.com/doi/full/10.1177/02783649241281508

    Uses DOI.org content negotiation to fetch BibTeX directly.
    """

    # DOI resolution endpoint
    DOI_API = "https://doi.org"

    # Pattern to match DOI URLs and extract the DOI
    # Matches both doi.org URLs and publisher URLs with /doi/ in the path
    DOI_PATTERN = re.compile(
        r"(?:(?:https?://)?(?:dx\.)?doi\.org/|doi:|/doi(?:/[a-z]+)*/)(10\.\d+/[^\s?#]+)"
    )

    def can_handle(self, url: str) -> bool:
        """Check if this is a DOI URL."""
        return self.DOI_PATTERN.search(url) is not None

    def extract_bibtex(self, url: str) -> Optional[str]:
        """Extract BibTeX entry from DOI URL."""
        # Extract DOI from URL
        match = self.DOI_PATTERN.search(url)
        if not match:
            return None

        doi = match.group(1)

        # Fetch BibTeX from DOI.org using content negotiation
        # DOI.org supports returning BibTeX directly when Accept header is set
        bibtex = fetch_with_retry(
            f"{self.DOI_API}/{doi}",
            accept_header='application/x-bibtex'
        )

        if not bibtex:
            return None

        # The response is already in BibTeX format (bytes)
        if isinstance(bibtex, bytes):
            bibtex = bibtex.decode('utf-8')

        # Clean up the BibTeX (sometimes has extra whitespace)
        bibtex = bibtex.strip()

        return bibtex if bibtex else None
