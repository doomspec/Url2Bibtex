"""URL parameter handler for BibTeX conversion."""

import re
from typing import Optional
from urllib.parse import parse_qs, urlparse, unquote
from ..handler import Handler


class UrlParamHandler(Handler):
    """
    Handler for URLs that contain BibTeX data in URL parameters.

    Supports URLs like:
    - https://example.com/page.html?bib=<encoded-bibtex>
    - https://www.daylight.com/dayhtml/doc/theory/theory.smarts.html?bib=%2540misc%257B...

    The handler extracts the 'bib' parameter and decodes it to return the BibTeX entry.
    """

    def can_handle(self, url: str) -> bool:
        """Check if this URL contains a 'bib' parameter."""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            return 'bib' in params
        except Exception:
            return False

    def extract_bibtex(self, url: str) -> Optional[str]:
        """Extract BibTeX entry from URL parameter."""
        try:
            # Parse the URL
            parsed = urlparse(url)
            params = parse_qs(parsed.query)

            # Get the 'bib' parameter
            if 'bib' not in params:
                return None
            # parse_qs returns a list of values for each parameter
            # We take the first value
            encoded_bibtex = params['bib'][0]

            # URL decode the BibTeX data
            # parse_qs already does one level of decoding, but we may need more
            decoded_bibtex = unquote(encoded_bibtex)

            # Clean up the BibTeX (remove extra whitespace)
            decoded_bibtex = decoded_bibtex.strip()

            print(decoded_bibtex)

            return decoded_bibtex if decoded_bibtex else None

        except Exception as e:
            return None
