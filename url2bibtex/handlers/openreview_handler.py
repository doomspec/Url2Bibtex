"""OpenReview URL handler for BibTeX conversion."""

import re
from typing import Optional
from ..handler import Handler
from ..utils import fetch_with_retry


class OpenReviewHandler(Handler):
    """
    Handler for OpenReview URLs.

    Supports URLs like:
    - https://openreview.net/forum?id=PAPER_ID
    - https://openreview.net/pdf?id=PAPER_ID
    """

    # OpenReview API endpoint
    OPENREVIEW_API = "https://api.openreview.net/notes"

    # Pattern to match OpenReview URLs and extract the paper ID
    OPENREVIEW_PATTERN = re.compile(
        r"openreview\.net/(?:forum|pdf)\?id=([a-zA-Z0-9_-]+)"
    )

    def can_handle(self, url: str) -> bool:
        """Check if this is an OpenReview URL."""
        return self.OPENREVIEW_PATTERN.search(url) is not None

    def extract_bibtex(self, url: str) -> Optional[str]:
        """Extract BibTeX entry from OpenReview URL."""
        # Extract paper ID from URL
        match = self.OPENREVIEW_PATTERN.search(url)
        if not match:
            return None

        paper_id = match.group(1)

        # Fetch metadata from OpenReview API with retry logic
        data = fetch_with_retry(self.OPENREVIEW_API, {"id": paper_id})
        if not data:
            return None

        # Parse response
        try:
            if not data.get('notes') or len(data['notes']) == 0:
                print(f"No paper found with ID: {paper_id}")
                return None

            note = data['notes'][0]
            content = note.get('content', {})

            # Extract metadata
            title = content.get('title', 'Unknown Title')
            if isinstance(title, list):
                title = title[0] if title else 'Unknown Title'
            title = title.strip().replace('\n', ' ')

            # Extract authors
            authors = content.get('authors', [])
            if isinstance(authors, str):
                authors = [authors]
            authors_str = ' and '.join(authors) if authors else 'Unknown Author'

            # Extract year from creation time (timestamp in milliseconds)
            year = "Unknown"
            if 'cdate' in note:
                timestamp = note['cdate']
                # Convert milliseconds to year
                from datetime import datetime
                year = str(datetime.fromtimestamp(timestamp / 1000).year)

            # Extract venue/forum
            venue = content.get('venue', '')
            if not venue:
                # Try to get from invitation
                invitation = note.get('invitation', '')
                if invitation:
                    # Parse venue from invitation string
                    venue_match = re.search(r'([^/]+)/\d{4}/Conference', invitation)
                    if venue_match:
                        venue = venue_match.group(1)

            # Generate BibTeX key (first author's last name + year)
            if authors:
                first_author = authors[0] if isinstance(authors, list) else authors
                # Handle names like "John Doe" or "Doe, John"
                if ',' in first_author:
                    first_author_last = first_author.split(',')[0].strip().lower()
                else:
                    first_author_last = first_author.split()[-1].lower()
                # Remove any non-alphanumeric characters
                first_author_last = re.sub(r'[^a-z0-9]', '', first_author_last)
                bibtex_key = f"{first_author_last}{year}"
            else:
                bibtex_key = f"openreview{year}"

            # Determine entry type based on venue
            entry_type = "inproceedings" if venue else "article"

            # Construct BibTeX entry
            bibtex_parts = [f"@{entry_type}{{{bibtex_key},"]
            bibtex_parts.append(f"  title = {{{title}}},")
            bibtex_parts.append(f"  author = {{{authors_str}}},")
            bibtex_parts.append(f"  year = {{{year}}},")

            if venue:
                bibtex_parts.append(f"  booktitle = {{{venue}}},")
            else:
                bibtex_parts.append(f"  journal = {{OpenReview}},")

            bibtex_parts.append(f"  url = {{https://openreview.net/forum?id={paper_id}}},")
            bibtex_parts.append(f"  note = {{OpenReview ID: {paper_id}}}")
            bibtex_parts.append("}")

            return '\n'.join(bibtex_parts)

        except (KeyError, IndexError, ValueError) as e:
            print(f"Error parsing OpenReview response: {e}")
            return None
