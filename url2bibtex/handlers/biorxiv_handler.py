"""bioRxiv URL handler for BibTeX conversion."""

import re
from typing import Optional
from ..handler import Handler
from .doi_handler import DOIHandler


class BioRxivHandler(Handler):
    """
    Handler for bioRxiv preprint URLs.

    Supports URLs like:
    - https://www.biorxiv.org/content/10.1101/2023.04.25.537981v2
    - https://biorxiv.org/content/10.1101/2023.04.25.537981v1
    - http://www.biorxiv.org/content/10.1101/2021.01.01.123456v3

    Extracts the DOI from the URL and uses the DOI handler to fetch
    the official BibTeX from DOI.org.
    """

    # Pattern to match bioRxiv URLs and extract the DOI
    # Matches URLs like: https://www.biorxiv.org/content/10.1101/2023.04.25.537981v2
    # Captures the DOI part (10.1101/...) and ignores version suffix (v1, v2, etc.)
    BIORXIV_PATTERN = re.compile(
        r"(?:https?://)?(?:www\.)?biorxiv\.org/content/(10\.1101/[\d.]+)(?:v\d+)?",
        re.IGNORECASE
    )

    def can_handle(self, url: str) -> bool:
        """Check if this is a bioRxiv URL."""
        return self.BIORXIV_PATTERN.search(url) is not None

    def extract_bibtex(self, url: str) -> Optional[str]:
        """Extract BibTeX entry from bioRxiv URL via DOI handler."""
        # Extract DOI from bioRxiv URL
        match = self.BIORXIV_PATTERN.search(url)
        if not match:
            return None

        doi = match.group(1)

        # Use DOI handler to fetch BibTeX
        doi_handler = DOIHandler()
        doi_url = f"https://doi.org/{doi}"

        return doi_handler.extract_bibtex(doi_url)
