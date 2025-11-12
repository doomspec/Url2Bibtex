"""GitHub URL handler for BibTeX conversion."""

import re
from typing import Optional
import requests
from ..handler import Handler
from ..utils import fetch_with_retry


class GitHubHandler(Handler):
    """
    Handler for GitHub repository URLs.

    Supports URLs like:
    - https://github.com/owner/repo
    - https://github.com/owner/repo/tree/branch

    Will attempt to:
    1. Parse CITATION.cff file if available
    2. Fall back to repository metadata from GitHub API
    """

    # GitHub API endpoint
    GITHUB_API = "https://api.github.com"

    # Pattern to match GitHub URLs and extract owner/repo
    GITHUB_PATTERN = re.compile(
        r"github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)"
    )

    def can_handle(self, url: str) -> bool:
        """Check if this is a GitHub URL."""
        return self.GITHUB_PATTERN.search(url) is not None

    def extract_bibtex(self, url: str) -> Optional[str]:
        """Extract BibTeX entry from GitHub URL."""
        # Extract owner and repo from URL
        match = self.GITHUB_PATTERN.search(url)
        if not match:
            return None

        owner = match.group(1)
        repo = match.group(2)

        # Try to get CITATION.cff first
        citation_bibtex = self._try_citation_cff(owner, repo)
        if citation_bibtex:
            return citation_bibtex

        # Fall back to repository metadata
        return self._get_repo_metadata_bibtex(owner, repo)

    def _try_citation_cff(self, owner: str, repo: str) -> Optional[str]:
        """Try to fetch and parse CITATION.cff file."""
        try:
            # Check if CITATION.cff exists
            response = requests.get(
                f"https://raw.githubusercontent.com/{owner}/{repo}/main/CITATION.cff",
                timeout=10
            )
            if response.status_code == 404:
                # Try master branch
                response = requests.get(
                    f"https://raw.githubusercontent.com/{owner}/{repo}/master/CITATION.cff",
                    timeout=10
                )

            if response.status_code == 200:
                # Parse CITATION.cff (simplified parsing)
                cff_content = response.text
                return self._parse_citation_cff(cff_content, owner, repo)
        except requests.RequestException:
            pass

        return None

    def _parse_citation_cff(self, cff_content: str, owner: str, repo: str) -> Optional[str]:
        """Parse CITATION.cff content to extract BibTeX information."""
        try:
            lines = cff_content.split('\n')
            metadata = {}

            # Simple YAML-like parsing
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    if key and value:
                        metadata[key] = value

            # Extract fields
            title = metadata.get('title', f"{owner}/{repo}")
            authors = []

            # Try to extract authors (simplified)
            in_authors = False
            current_author = {}
            for line in lines:
                if line.strip().startswith('authors:'):
                    in_authors = True
                    continue
                if in_authors:
                    if line.strip().startswith('-'):
                        if current_author:
                            authors.append(current_author)
                        current_author = {}
                    elif 'family-names:' in line:
                        current_author['family'] = line.split(':', 1)[1].strip().strip('"\'')
                    elif 'given-names:' in line:
                        current_author['given'] = line.split(':', 1)[1].strip().strip('"\'')
                    elif line.strip() and not line.strip().startswith(' ') and ':' in line:
                        # End of authors section
                        if current_author:
                            authors.append(current_author)
                        break

            if current_author and current_author not in authors:
                authors.append(current_author)

            # Format authors for BibTeX
            if authors:
                author_list = []
                for author in authors:
                    if 'given' in author and 'family' in author:
                        author_list.append(f"{author['given']} {author['family']}")
                    elif 'family' in author:
                        author_list.append(author['family'])
                authors_str = ' and '.join(author_list)
            else:
                authors_str = owner

            year = metadata.get('date-released', metadata.get('year', 'Unknown'))
            if year and len(year) >= 4:
                year = year[:4]

            # Generate BibTeX key
            first_author = authors[0]['family'] if authors and 'family' in authors[0] else owner
            first_author_clean = re.sub(r'[^a-z0-9]', '', first_author.lower())
            bibtex_key = f"{first_author_clean}{year}"

            # Construct BibTeX
            bibtex = f"""@software{{{bibtex_key},
  title = {{{title}}},
  author = {{{authors_str}}},
  year = {{{year}}},
  url = {{https://github.com/{owner}/{repo}}},
  note = {{GitHub repository}}
}}"""
            return bibtex

        except Exception as e:
            print(f"Error parsing CITATION.cff: {e}")
            return None

    def _get_repo_metadata_bibtex(self, owner: str, repo: str) -> Optional[str]:
        """Generate BibTeX from GitHub repository metadata."""
        # Fetch repository metadata
        data = fetch_with_retry(
            f"{self.GITHUB_API}/repos/{owner}/{repo}",
            accept_header="application/vnd.github.v3+json"
        )
        if not data:
            return None

        try:
            # Extract metadata
            name = data.get('name', repo)
            description = data.get('description', '')
            created_at = data.get('created_at', '')
            year = created_at[:4] if created_at else 'Unknown'

            # Get owner information
            owner_data = data.get('owner', {})
            owner_name = owner_data.get('login', owner)

            # Try to get contributors
            contributors = fetch_with_retry(
                f"{self.GITHUB_API}/repos/{owner}/{repo}/contributors",
                params={"per_page": 5},
                accept_header="application/vnd.github.v3+json"
            )
            if contributors:
                author_list = [c.get('login', '') for c in contributors[:5] if c.get('login')]
                authors_str = ' and '.join(author_list) if author_list else owner_name
            else:
                authors_str = owner_name

            # Generate BibTeX key
            first_author = authors_str.split(' and ')[0] if ' and ' in authors_str else authors_str
            first_author_clean = re.sub(r'[^a-z0-9]', '', first_author.lower())
            bibtex_key = f"{first_author_clean}{year}"

            # Construct BibTeX
            bibtex_parts = [f"@software{{{bibtex_key},"]
            bibtex_parts.append(f"  title = {{{name}}},")
            bibtex_parts.append(f"  author = {{{authors_str}}},")
            bibtex_parts.append(f"  year = {{{year}}},")
            if description:
                bibtex_parts.append(f"  note = {{{description}}},")
            bibtex_parts.append(f"  url = {{https://github.com/{owner}/{repo}}},")
            bibtex_parts.append(f"  publisher = {{GitHub}}")
            bibtex_parts.append("}")

            return '\n'.join(bibtex_parts)

        except (KeyError, ValueError) as e:
            print(f"Error parsing GitHub repository data: {e}")
            return None
