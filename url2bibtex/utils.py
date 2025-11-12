"""Utility functions for url2bibtex."""

import time
import random
from typing import Optional, Union
import requests


# Create a session for cookie handling and connection pooling
_session = None


def get_session() -> requests.Session:
    """Get or create a shared requests session."""
    global _session
    if _session is None:
        _session = requests.Session()
        # Enable connection pooling and keep-alive
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=0  # We handle retries ourselves
        )
        _session.mount('http://', adapter)
        _session.mount('https://', adapter)
    return _session


def get_browser_headers(accept_header: str = 'application/json') -> dict:
    """
    Generate realistic browser headers to bypass anti-bot measures.

    Args:
        accept_header: The Accept header value

    Returns:
        Dictionary of HTTP headers that mimic a real browser
    """
    # Use a realistic User-Agent from a common browser
    user_agents = [
        # Chrome on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # Chrome on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # Firefox on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        # Safari on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    ]

    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': accept_header,
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',  # Do Not Track
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }

    # Add referer for HTML requests to look more natural
    if 'text/html' in accept_header or accept_header == 'text/html':
        headers['Referer'] = 'https://www.google.com/'

    return headers


def fetch_with_retry(
    url: str,
    params: Optional[dict] = None,
    max_retries: int = 3,
    timeout: int = 20,
    accept_header: str = 'application/json',
    use_browser_headers: bool = True
) -> Optional[Union[dict, bytes]]:
    """
    Fetch data from URL with exponential backoff retry logic and browser-like behavior.

    This function mimics browser behavior to bypass anti-bot measures by:
    - Using realistic browser User-Agent strings
    - Including standard browser headers
    - Managing cookies via sessions
    - Following redirects properly
    - Adding small random delays

    Args:
        url: The URL to fetch
        params: Query parameters
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
        accept_header: Accept header value (e.g., 'application/json', 'text/html')
        use_browser_headers: Use realistic browser headers (recommended for HTML pages)

    Returns:
        Response content (JSON dict or bytes) or None if all retries failed
    """
    session = get_session()

    for attempt in range(max_retries):
        try:
            # Generate headers
            if use_browser_headers:
                headers = get_browser_headers(accept_header)
            else:
                headers = {
                    'User-Agent': 'url2bibtex/0.1.0 (Academic Citation Tool)',
                    'Accept': accept_header
                }

            # Add small random delay to avoid looking like a bot (except first attempt)
            if attempt > 0:
                time.sleep(random.uniform(0.5, 1.5))

            response = session.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout,
                allow_redirects=True,
                verify=True  # Verify SSL certificates
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 2 ** attempt))
                print(f"Rate limited. Waiting {retry_after} seconds before retry...")
                time.sleep(retry_after)
                continue

            # Handle 403 Forbidden - might be anti-bot
            if response.status_code == 403:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt + random.uniform(1, 3)
                    print(f"Access forbidden (403). Retrying with different headers in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    # Force regenerate headers on retry
                    continue
                else:
                    print(f"Access forbidden (403) after {max_retries} attempts. The site may be blocking automated requests.")
                    return None

            response.raise_for_status()

            # Return JSON if content type is JSON, otherwise return bytes
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return response.json()
            else:
                return response.content

        except requests.exceptions.SSLError as e:
            print(f"SSL verification failed: {e}")
            if attempt == max_retries - 1:
                return None
            time.sleep(2 ** attempt)

        except requests.exceptions.Timeout as e:
            print(f"Request timeout: {e}")
            if attempt == max_retries - 1:
                return None
            time.sleep(2 ** attempt)

        except requests.RequestException as e:
            if attempt == max_retries - 1:
                print(f"Error fetching data after {max_retries} attempts: {e}")
                return None

            # Exponential backoff with jitter
            wait_time = 2 ** attempt + random.uniform(0, 1)
            print(f"Request failed. Retrying in {wait_time:.1f} seconds... (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait_time)

    return None
