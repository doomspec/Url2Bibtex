"""HTML Meta Tags handler for BibTeX conversion (fallback handler)."""

import re
from typing import Optional
from datetime import datetime
from ..handler import Handler
from ..utils import fetch_with_retry


class HTMLMetaHandler(Handler):
    """
    Fallback handler that extracts BibTeX from HTML meta tags.

    This handler works with any website that includes citation metadata
    in HTML meta tags (citation_*, DC.*, og:*, etc.). It should be
    registered last as a fallback for URLs not handled by specific handlers.

    Supported meta tag formats:
    - citation_* (Google Scholar format, used by many publishers)
    - DC.* (Dublin Core)
    - og:* (Open Graph)
    """

    def can_handle(self, url: str) -> bool:
        """
        This is a fallback handler that can handle any HTTP(S) URL.
        Should be registered last to avoid overriding specific handlers.
        """
        return url.startswith('http://') or url.startswith('https://')

    def extract_bibtex(self, url: str) -> Optional[str]:
        """Extract BibTeX entry from HTML meta tags."""
        # Fetch HTML content
        html_content = fetch_with_retry(url, accept_header='text/html')
        if not html_content:
            return None

        # Convert bytes to string if needed
        if isinstance(html_content, bytes):
            try:
                html_content = html_content.decode('utf-8')
            except UnicodeDecodeError:
                html_content = html_content.decode('latin-1')

        # Parse meta tags
        metadata = self._parse_meta_tags(html_content)
        if not metadata.get('title'):
            return None

        # Generate BibTeX from metadata
        return self._generate_bibtex(metadata, url)

    def _parse_meta_tags(self, html: str) -> dict:
        """Parse meta tags from HTML content."""
        metadata = {
            'title': None,
            'authors': [],
            'year': None,
            'journal': None,
            'volume': None,
            'issue': None,
            'pages': None,
            'doi': None,
            'abstract': None,
            'publisher': None,
            'isbn': None,
            'issn': None
        }

        # Simple regex-based parsing (no external dependencies)
        # Look for meta tags with name or property attributes
        meta_pattern = re.compile(
            r'<meta\s+(?:name|property)=["\']([^"\']+)["\']\s+content=["\']([^"\']+)["\']',
            re.IGNORECASE
        )

        for match in meta_pattern.finditer(html):
            name = match.group(1).lower()
            content = match.group(2).strip()

            if not content:
                continue

            # Citation tags (Google Scholar format)
            if name == 'citation_title' or name == 'dc.title':
                metadata['title'] = content
            elif name == 'citation_author' or name == 'dc.creator' or name == 'author':
                metadata['authors'].append(content)
            elif name in ['citation_publication_date', 'citation_date', 'dc.date', 'article:published_time']:
                # Extract year from date
                year_match = re.search(r'(\d{4})', content)
                if year_match:
                    metadata['year'] = year_match.group(1)
            elif name in ['citation_journal_title', 'citation_conference_title', 'dc.source']:
                metadata['journal'] = content
            elif name == 'citation_volume':
                metadata['volume'] = content
            elif name == 'citation_issue':
                metadata['issue'] = content
            elif name == 'citation_firstpage':
                metadata['pages'] = content
            elif name == 'citation_lastpage' and metadata['pages']:
                metadata['pages'] += f"--{content}"
            elif name in ['citation_doi', 'dc.identifier.doi']:
                # Clean DOI
                doi = content.replace('https://doi.org/', '').replace('http://doi.org/', '')
                metadata['doi'] = doi
            elif name in ['citation_abstract', 'dc.description', 'og:description']:
                if not metadata['abstract']:  # Use first abstract found
                    metadata['abstract'] = content
            elif name in ['citation_publisher', 'dc.publisher']:
                metadata['publisher'] = content
            elif name == 'citation_isbn':
                metadata['isbn'] = content
            elif name == 'citation_issn':
                metadata['issn'] = content

        return metadata

    def _generate_bibtex(self, metadata: dict, url: str) -> Optional[str]:
        """Generate BibTeX entry from metadata."""
        title = metadata.get('title')
        if not title:
            return None

        # Determine entry type
        if metadata.get('journal'):
            entry_type = 'article'
        else:
            entry_type = 'misc'

        # Format authors
        authors = metadata.get('authors', [])
        if authors:
            authors_str = ' and '.join(authors)
        else:
            authors_str = 'Unknown Author'

        # Generate BibTeX key
        year = metadata.get('year', datetime.now().year)
        if authors:
            first_author = authors[0]
            # Handle names like "John Doe" or "Doe, John"
            if ',' in first_author:
                first_author_last = first_author.split(',')[0].strip().lower()
            else:
                parts = first_author.split()
                first_author_last = parts[-1].lower() if parts else 'unknown'
            # Remove any non-alphanumeric characters
            first_author_last = re.sub(r'[^a-z0-9]', '', first_author_last)
            bibtex_key = f"{first_author_last}{year}"
        else:
            bibtex_key = f"web{year}"

        # Build BibTeX entry
        bibtex_parts = [f"@{entry_type}{{{bibtex_key},"]
        bibtex_parts.append(f"  title = {{{title}}},")
        bibtex_parts.append(f"  author = {{{authors_str}}},")
        bibtex_parts.append(f"  year = {{{year}}},")

        if metadata.get('journal'):
            bibtex_parts.append(f"  journal = {{{metadata['journal']}}},")

        if metadata.get('volume'):
            bibtex_parts.append(f"  volume = {{{metadata['volume']}}},")

        if metadata.get('issue'):
            bibtex_parts.append(f"  number = {{{metadata['issue']}}},")

        if metadata.get('pages'):
            bibtex_parts.append(f"  pages = {{{metadata['pages']}}},")

        if metadata.get('doi'):
            bibtex_parts.append(f"  doi = {{{metadata['doi']}}},")

        if metadata.get('publisher'):
            bibtex_parts.append(f"  publisher = {{{metadata['publisher']}}},")

        if metadata.get('issn'):
            bibtex_parts.append(f"  issn = {{{metadata['issn']}}},")

        if metadata.get('isbn'):
            bibtex_parts.append(f"  isbn = {{{metadata['isbn']}}},")

        bibtex_parts.append(f"  url = {{{url}}}")
        bibtex_parts.append("}")

        return '\n'.join(bibtex_parts)
