"""Semantic Scholar URL handler for BibTeX conversion."""

import re
from typing import Optional
from ..handler import Handler
from ..utils import fetch_with_retry
from .doi_handler import DOIHandler


class SemanticScholarHandler(Handler):
    """
    Handler for Semantic Scholar URLs.

    Supports URLs like:
    - https://www.semanticscholar.org/paper/{title-slug}/{paper-id}
    """

    # Semantic Scholar API endpoint
    SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper"

    # Pattern to match Semantic Scholar URLs and extract the paper ID
    SEMANTIC_SCHOLAR_PATTERN = re.compile(
        r"semanticscholar\.org/paper/[^/]+/([a-f0-9]+)"
    )

    def can_handle(self, url: str) -> bool:
        """Check if this is a Semantic Scholar URL."""
        return self.SEMANTIC_SCHOLAR_PATTERN.search(url) is not None

    def extract_bibtex(self, url: str) -> Optional[str]:
        """Extract BibTeX entry from Semantic Scholar URL."""
        # Extract paper ID from URL
        match = self.SEMANTIC_SCHOLAR_PATTERN.search(url)
        if not match:
            return None

        paper_id = match.group(1)

        # Define fields to fetch from API
        fields = "title,authors,year,venue,publicationVenue,externalIds,publicationTypes,journal,citationCount"

        # Fetch metadata from Semantic Scholar API with retry logic
        data = fetch_with_retry(
            f"{self.SEMANTIC_SCHOLAR_API}/{paper_id}",
            {"fields": fields}
        )
        if not data:
            return None

        # Parse response
        try:
            # Extract metadata
            title = data.get('title', 'Unknown Title')
            title = title.strip().replace('\n', ' ')

            # Extract authors
            authors_data = data.get('authors', [])
            if authors_data:
                author_list = [author.get('name', '') for author in authors_data if author.get('name')]
                authors_str = ' and '.join(author_list)
            else:
                authors_str = 'Unknown Author'

            # Extract year
            year = data.get('year')
            if year is None:
                year = 'Unknown'
            else:
                year = str(year)

            # Extract venue information
            venue = data.get('venue', '')
            publication_venue = data.get('publicationVenue', {})
            if not venue and publication_venue:
                venue = publication_venue.get('name', '')

            # Extract journal information
            journal_info = data.get('journal')
            journal_name = None
            if journal_info:
                journal_name = journal_info.get('name')

            # Extract DOI and ArXiv ID if available
            external_ids = data.get('externalIds', {})
            doi = external_ids.get('DOI')
            arxiv_id = external_ids.get('ArXiv')

            # If DOI is available, use DOI handler to generate BibTeX
            if doi:
                doi_handler = DOIHandler()
                doi_url = f"https://doi.org/{doi}"
                bibtex = doi_handler.extract_bibtex(doi_url)
                if bibtex:
                    return bibtex
                # If DOI handler fails, fall through to manual generation below

            # Determine publication type
            pub_types = data.get('publicationTypes', [])

            # Generate BibTeX key (first author's last name + year)
            if author_list:
                first_author = author_list[0]
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
                bibtex_key = f"semanticscholar{year}"

            # Determine entry type
            entry_type = "article"
            if pub_types:
                if 'Conference' in pub_types or 'JournalArticle' in pub_types:
                    if 'Conference' in pub_types:
                        entry_type = "inproceedings"
                elif 'Book' in pub_types:
                    entry_type = "book"

            # Construct BibTeX entry
            bibtex_parts = [f"@{entry_type}{{{bibtex_key},"]
            bibtex_parts.append(f"  title = {{{title}}},")
            bibtex_parts.append(f"  author = {{{authors_str}}},")
            bibtex_parts.append(f"  year = {{{year}}},")

            # Add venue or journal
            if entry_type == "inproceedings" and venue:
                bibtex_parts.append(f"  booktitle = {{{venue}}},")
            elif entry_type == "article":
                if journal_name:
                    bibtex_parts.append(f"  journal = {{{journal_name}}},")
                elif venue:
                    bibtex_parts.append(f"  journal = {{{venue}}},")

            # Add DOI if available
            if doi:
                bibtex_parts.append(f"  doi = {{{doi}}},")

            # Add arXiv ID if available
            if arxiv_id:
                bibtex_parts.append(f"  eprint = {{{arxiv_id}}},")
                bibtex_parts.append(f"  archivePrefix = {{arXiv}},")
            if not doi:
                # Add Semantic Scholar URL
                bibtex_parts.append(f"  url = {{https://www.semanticscholar.org/paper/{paper_id}}}")
            else:
                # Add DOI URL
                bibtex_parts.append(f"  url = {{https://doi.org/{doi}}}")

            bibtex_parts.append("}")

            return '\n'.join(bibtex_parts)

        except (KeyError, ValueError) as e:
            print(f"Error parsing Semantic Scholar response: {e}")
            return None
