#!/usr/bin/env python3
"""Example usage of url2bibtex package."""

from url2bibtex import Url2Bibtex, ACLAnthologyHandler, IEEEHandler
from url2bibtex.handlers import (
    ArxivHandler, OpenReviewHandler, SemanticScholarHandler,
    GitHubHandler, DOIHandler, HTMLMetaHandler
)


def main():
    """Demonstrate url2bibtex functionality."""
    # Create converter instance
    converter = Url2Bibtex()

    # Register specific handlers first
    converter.register_handler(IEEEHandler())
    converter.register_handler(ACLAnthologyHandler())
    converter.register_handler(HTMLMetaHandler())

    # Example URLs
    test_urls = [
        "https://ieeexplore.ieee.org/document/10897629",
        "https://dspace.mit.edu/handle/1721.1/127290",
        "https://www.nature.com/articles/s41586-020-2649-2",  # Nature article
        "https://aclanthology.org/2024.findings-emnlp.746"
    ]

    print("=" * 80)
    print("url2bibtex - Example Usage")
    print("=" * 80)
    print()

    for url in test_urls:
        print(f"Converting: {url}")
        print("-" * 80)

        # Check if URL can be converted
        if converter.can_convert(url):
            try:
                # Convert URL to BibTeX
                bibtex = converter.convert(url)
                if bibtex:
                    print(bibtex)
                else:
                    print(f"Failed to extract BibTeX from: {url}")
            except Exception as e:
                print(f"Error converting URL: {e}")
        else:
            print(f"No handler available for: {url}")

        print()
        print()


if __name__ == "__main__":
    main()
