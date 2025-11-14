"""GitHub, GitLab, and Zenodo URL handler for BibTeX conversion."""

import re
import urllib.parse
from typing import Optional
import requests
from ..handler import Handler
from ..utils import fetch_with_retry


class GitHubHandler(Handler):
    """
    Handler for GitHub, GitLab, and Zenodo URLs.

    Supports URLs like:
    - GitHub: https://github.com/owner/repo
    - GitLab: https://gitlab.com/owner/repo
    - Zenodo: https://zenodo.org/record/1234567 or https://doi.org/10.5281/zenodo.1234567

    Will attempt to:
    1. For GitHub/GitLab: Parse CITATION.cff file if available, fall back to API metadata
    2. For Zenodo: Fetch metadata from Zenodo API using record ID
    """

    # API endpoints
    GITHUB_API = "https://api.github.com"
    GITLAB_API = "https://gitlab.com/api/v4"
    ZENODO_API = "https://zenodo.org/api"

    # Patterns to match URLs
    GITHUB_PATTERN = re.compile(
        r"github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)"
    )
    GITLAB_PATTERN = re.compile(
        r"gitlab\.com/([a-zA-Z0-9_-]+(?:/[a-zA-Z0-9_.-]+)*)"
    )
    ZENODO_PATTERN = re.compile(
        r"(?:zenodo\.org/record[s]?/(\d+)|doi\.org/10\.5281/zenodo\.(\d+))"
    )

    def can_handle(self, url: str) -> bool:
        """Check if this is a GitHub, GitLab, or Zenodo URL."""
        return (self.GITHUB_PATTERN.search(url) is not None or
                self.GITLAB_PATTERN.search(url) is not None or
                self.ZENODO_PATTERN.search(url) is not None)

    def extract_bibtex(self, url: str) -> Optional[str]:
        """Extract BibTeX entry from GitHub, GitLab, or Zenodo URL."""
        # Check which platform this URL is from
        if self.ZENODO_PATTERN.search(url):
            return self._extract_zenodo(url)
        elif self.GITLAB_PATTERN.search(url):
            return self._extract_gitlab(url)
        elif self.GITHUB_PATTERN.search(url):
            return self._extract_github(url)

        return None

    def _extract_github(self, url: str) -> Optional[str]:
        """Extract BibTeX entry from GitHub URL."""
        # Extract owner and repo from URL
        match = self.GITHUB_PATTERN.search(url)
        if not match:
            return None

        owner = match.group(1)
        repo = match.group(2)

        # Try to get CITATION.cff first
        citation_bibtex = self._try_citation_cff(owner, repo, url, platform="github")
        if citation_bibtex:
            return citation_bibtex

        # Fall back to repository metadata
        return self._get_github_metadata_bibtex(owner, repo, url)

    def _try_citation_cff(self, owner: str, repo: str, original_url: str, platform: str = "github") -> Optional[str]:
        """Try to fetch and parse CITATION.cff file."""
        try:
            if platform == "github":
                base_url = f"https://raw.githubusercontent.com/{owner}/{repo}"
            elif platform == "gitlab":
                # For GitLab, we need to URL-encode the project path
                project_path = f"{owner}"
                base_url = f"https://gitlab.com/{project_path}/-/raw"
            else:
                return None

            # Check if CITATION.cff exists (try main and master branches)
            for branch in ["main", "master"]:
                try:
                    response = requests.get(
                        f"{base_url}/{branch}/CITATION.cff",
                        timeout=10
                    )
                    if response.status_code == 200:
                        # Parse CITATION.cff (simplified parsing)
                        cff_content = response.text
                        return self._parse_citation_cff(cff_content, owner, repo, original_url, platform)
                except requests.RequestException:
                    continue

        except requests.RequestException:
            pass

        return None

    def _parse_citation_cff(self, cff_content: str, owner: str, repo: str, original_url: str, platform: str = "github") -> Optional[str]:
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
            title = metadata.get('title', f"{owner}/{repo}" if repo else owner)
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
            first_author = authors[0]['family'] if authors and 'family' in authors[0] else owner.split('/')[0]
            first_author_clean = re.sub(r'[^a-z0-9]', '', first_author.lower())
            bibtex_key = f"{first_author_clean}{year}"

            # Use original URL and set note based on platform
            if platform == "gitlab":
                note = "GitLab repository"
            else:
                note = "GitHub repository"

            # author field is removed
            bibtex = f"""@software{{{bibtex_key},
  title = {{{title}}},
  year = {{{year}}},
  url = {{{original_url}}},
  note = {{{note}}}
}}"""
            return bibtex

        except Exception as e:
            print(f"Error parsing CITATION.cff: {e}")
            return None

    def _get_github_metadata_bibtex(self, owner: str, repo: str, original_url: str) -> Optional[str]:
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

            # Construct BibTeX with original URL
            bibtex_parts = [f"@software{{{bibtex_key},"]
            bibtex_parts.append(f"  title = {{{name}}},")
            bibtex_parts.append(f"  author = {{{authors_str}}},")
            bibtex_parts.append(f"  year = {{{year}}},")
            if description:
                bibtex_parts.append(f"  note = {{{description}}},")
            bibtex_parts.append(f"  url = {{{original_url}}},")
            bibtex_parts.append(f"  publisher = {{GitHub}}")
            bibtex_parts.append("}")

            return '\n'.join(bibtex_parts)

        except (KeyError, ValueError) as e:
            print(f"Error parsing GitHub repository data: {e}")
            return None

    def _extract_gitlab(self, url: str) -> Optional[str]:
        """Extract BibTeX entry from GitLab URL."""
        # Extract project path from URL
        match = self.GITLAB_PATTERN.search(url)
        if not match:
            return None

        project_path = match.group(1)

        # Try to get CITATION.cff first
        # Split path for owner and repo (last part is repo name)
        path_parts = project_path.split('/')
        if len(path_parts) >= 2:
            repo = path_parts[-1]
            citation_bibtex = self._try_citation_cff(project_path, repo, url, platform="gitlab")
            if citation_bibtex:
                return citation_bibtex

        # Fall back to repository metadata
        return self._get_gitlab_metadata_bibtex(project_path, url)

    def _get_gitlab_metadata_bibtex(self, project_path: str, original_url: str) -> Optional[str]:
        """Generate BibTeX from GitLab repository metadata."""
        # URL-encode the project path
        encoded_path = urllib.parse.quote(project_path, safe='')

        # Fetch repository metadata
        data = fetch_with_retry(
            f"{self.GITLAB_API}/projects/{encoded_path}",
            accept_header="application/json"
        )
        if not data:
            return None

        try:
            # Extract metadata
            name = data.get('name', project_path.split('/')[-1])
            description = data.get('description', '')
            created_at = data.get('created_at', '')
            year = created_at[:4] if created_at else 'Unknown'

            # Get owner information
            namespace = data.get('namespace', {})
            owner_name = namespace.get('name', project_path.split('/')[0])

            # Try to get contributors
            contributors = fetch_with_retry(
                f"{self.GITLAB_API}/projects/{encoded_path}/repository/contributors",
                params={"per_page": 5},
                accept_header="application/json"
            )
            if contributors:
                author_list = [c.get('name', c.get('username', '')) for c in contributors[:5] if c.get('name') or c.get('username')]
                authors_str = ' and '.join(author_list) if author_list else owner_name
            else:
                authors_str = owner_name

            # Generate BibTeX key
            first_author = authors_str.split(' and ')[0] if ' and ' in authors_str else authors_str
            first_author_clean = re.sub(r'[^a-z0-9]', '', first_author.lower())
            bibtex_key = f"{first_author_clean}{year}"

            # Construct BibTeX with original URL
            bibtex_parts = [f"@software{{{bibtex_key},"]
            bibtex_parts.append(f"  title = {{{name}}},")
            #bibtex_parts.append(f"  author = {{{authors_str}}},")
            bibtex_parts.append(f"  year = {{{year}}},")
            if description:
                bibtex_parts.append(f"  note = {{{description}}},")
            bibtex_parts.append(f"  url = {{{original_url}}},")
            bibtex_parts.append(f"  publisher = {{GitLab}}")
            bibtex_parts.append("}")

            return '\n'.join(bibtex_parts)

        except (KeyError, ValueError) as e:
            print(f"Error parsing GitLab repository data: {e}")
            return None

    def _extract_zenodo(self, url: str) -> Optional[str]:
        """Extract BibTeX entry from Zenodo URL."""
        # Extract record ID from URL
        match = self.ZENODO_PATTERN.search(url)
        if not match:
            return None

        # Get the record ID (either from group 1 or 2)
        record_id = match.group(1) or match.group(2)

        # Fetch record metadata from Zenodo API
        data = fetch_with_retry(
            f"{self.ZENODO_API}/records/{record_id}",
            accept_header="application/json"
        )
        if not data:
            return None

        try:
            # Extract metadata
            metadata = data.get('metadata', {})

            # Title
            title = metadata.get('title', 'Unknown Title')

            # Authors
            creators = metadata.get('creators', [])
            if creators:
                author_list = []
                for creator in creators:
                    name = creator.get('name', '')
                    if name:
                        author_list.append(name)
                authors_str = ' and '.join(author_list) if author_list else 'Unknown'
            else:
                authors_str = 'Unknown'

            # Year
            publication_date = metadata.get('publication_date', '')
            year = publication_date[:4] if publication_date else 'Unknown'

            # DOI
            doi = data.get('doi', metadata.get('doi', ''))

            # Resource type
            resource_type = metadata.get('resource_type', {})
            entry_type = resource_type.get('type', 'misc')

            # Map Zenodo resource types to BibTeX entry types
            type_mapping = {
                'publication': 'article',
                'poster': 'misc',
                'presentation': 'misc',
                'dataset': 'misc',
                'image': 'misc',
                'video': 'misc',
                'software': 'software',
                'lesson': 'misc',
                'other': 'misc'
            }
            bibtex_type = type_mapping.get(entry_type.lower(), 'misc')

            # Generate BibTeX key
            first_author = authors_str.split(' and ')[0] if ' and ' in authors_str else authors_str
            # Extract last name if format is "Last, First"
            if ',' in first_author:
                first_author = first_author.split(',')[0].strip()
            first_author_clean = re.sub(r'[^a-z0-9]', '', first_author.lower())
            bibtex_key = f"{first_author_clean}{year}"

            # Construct BibTeX with original URL
            bibtex_parts = [f"@{bibtex_type}{{{bibtex_key},"]
            bibtex_parts.append(f"  title = {{{title}}},")
            bibtex_parts.append(f"  author = {{{authors_str}}},")
            bibtex_parts.append(f"  year = {{{year}}},")

            # Include DOI if available
            if doi:
                bibtex_parts.append(f"  doi = {{{doi}}},")

            # Always use the original URL
            bibtex_parts.append(f"  url = {{{url}}},")
            bibtex_parts.append(f"  publisher = {{Zenodo}}")
            bibtex_parts.append("}")

            return '\n'.join(bibtex_parts)

        except (KeyError, ValueError) as e:
            print(f"Error parsing Zenodo record data: {e}")
            return None
