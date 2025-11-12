"""Utility functions for url2bibtex."""

import time
from typing import Optional, Union
import requests


def fetch_with_retry(
    url: str,
    params: Optional[dict] = None,
    max_retries: int = 3,
    timeout: int = 15,
    accept_header: str = 'application/json'
) -> Optional[Union[dict, bytes]]:
    """
    Fetch data from URL with exponential backoff retry logic.

    Args:
        url: The URL to fetch
        params: Query parameters
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
        accept_header: Accept header value (e.g., 'application/json', 'application/atom+xml')

    Returns:
        Response content (JSON dict or bytes) or None if all retries failed
    """
    headers = {
        'User-Agent': 'url2bibtex/0.1.0 (https://github.com/yourusername/url2bibtex)',
        'Accept': accept_header
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 2 ** attempt))
                print(f"Rate limited. Waiting {retry_after} seconds before retry...")
                time.sleep(retry_after)
                continue

            response.raise_for_status()

            # Return JSON if content type is JSON, otherwise return bytes
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return response.json()
            else:
                return response.content

        except requests.RequestException as e:
            if attempt == max_retries - 1:
                print(f"Error fetching data after {max_retries} attempts: {e}")
                return None

            # Exponential backoff
            wait_time = 2 ** attempt
            print(f"Request failed. Retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait_time)

    return None
