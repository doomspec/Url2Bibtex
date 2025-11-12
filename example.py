#!/usr/bin/env python3
"""Example usage of url2bibtex package."""

from url2bibtex import Url2Bibtex
from url2bibtex.handlers import ArxivHandler, OpenReviewHandler, SemanticScholarHandler, GitHubHandler, DOIHandler


def main():
    """Demonstrate url2bibtex functionality."""
    # Create converter instance
    converter = Url2Bibtex()

    # Register handlers
    converter.register_handler(ArxivHandler())
    converter.register_handler(OpenReviewHandler())
    converter.register_handler(SemanticScholarHandler())
    converter.register_handler(GitHubHandler())
    converter.register_handler(DOIHandler())

    # Example URLs
    test_urls = [
        # ArXiv URLs
        "https://arxiv.org/abs/2103.15348",  # DeiT paper
        "https://arxiv.org/abs/1706.03762",  # Attention is All You Need
        "https://arxiv.org/pdf/2010.11929.pdf",  # Vision Transformer

        # OpenReview URLs
        "https://openreview.net/forum?id=YicbFdNTTy",  # Example OpenReview paper

        # Semantic Scholar URLs
        "https://www.semanticscholar.org/paper/Epistemology-of-the-Closet-Sedgwick/f235ba0e7b4ca7f5fab23dfa05a8300596d0b857",

        # DOI URLs
        "https://doi.org/10.1038/nature12373",  # Nature paper

        # GitHub URLs
        "https://github.com/pytorch/pytorch",  # PyTorch repository
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
