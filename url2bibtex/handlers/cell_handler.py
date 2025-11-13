"""Cell.com URL handler for BibTeX conversion."""

import re
from typing import Optional
from ..handler import Handler
from .pii_handler import PIIHandler


class CellHandler(Handler):
    """
    Handler for Cell.com URLs containing PII.

    Supports URLs like:
    - https://www.cell.com/cell/fulltext/S0092-8674(25)00927-4
    - https://www.cell.com/molecular-cell/fulltext/S1097-2765(24)00123-4

    Will:
    1. Extract the PII from the URL (format: S0092-8674(25)00927-4)
    2. Normalize it by removing parentheses and hyphens (S0092867425009274)
    3. Use PII handler to fetch BibTeX via CrossRef API
    """

    # Pattern to match Cell.com URLs with PII
    CELL_PATTERN = re.compile(
        r"cell\.com/[^/]+/fulltext/(S\d{4}-\d{4}\(\d{2}\)\d{5}-\d)"
    )

    def __init__(self):
        """Initialize Cell handler with PII handler for BibTeX fetching."""
        super().__init__()
        self.pii_handler = PIIHandler()

    def can_handle(self, url: str) -> bool:
        """Check if this is a Cell.com URL."""
        return self.CELL_PATTERN.search(url) is not None

    def extract_bibtex(self, url: str) -> Optional[str]:
        """Extract BibTeX entry from Cell.com URL."""
        # Extract PII from URL
        match = self.CELL_PATTERN.search(url)
        if not match:
            return None

        pii_formatted = match.group(1)

        # Normalize PII by removing parentheses and hyphens
        # From: S0092-8674(25)00927-4
        # To: S0092867425009274
        pii = self._normalize_pii(pii_formatted)

        # Use PII handler to fetch BibTeX
        # Create a fake ScienceDirect URL that the PII handler can process
        fake_url = f"https://www.sciencedirect.com/science/article/pii/{pii}"
        bibtex = self.pii_handler.extract_bibtex(fake_url)

        return bibtex

    def _normalize_pii(self, pii_formatted: str) -> str:
        """
        Normalize PII by removing parentheses and hyphens.

        Args:
            pii_formatted: PII in Cell format (e.g., S0092-8674(25)00927-4)

        Returns:
            Normalized PII (e.g., S0092867425009274)
        """
        # Remove all parentheses and hyphens
        pii = pii_formatted.replace('(', '').replace(')', '').replace('-', '')
        return pii
