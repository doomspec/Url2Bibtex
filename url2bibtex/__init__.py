"""
url2bibtex - Convert paper URLs to BibTeX entries.

This package provides a framework for converting URLs to academic papers
into BibTeX entries. It supports a pluggable handler system that allows
you to add custom handlers for different types of URLs.

Example:
    >>> from url2bibtex import Url2Bibtex
    >>> from url2bibtex.handlers import ArxivHandler
    >>>
    >>> converter = Url2Bibtex()
    >>> converter.register_handler(ArxivHandler())
    >>>
    >>> url = "https://arxiv.org/abs/2103.15348"
    >>> bibtex = converter.convert(url)
    >>> print(bibtex)
"""

from .converter import Url2Bibtex
from .handler import Handler, HandlerRegistry
from .handlers import ArxivHandler, OpenReviewHandler, SemanticScholarHandler, GitHubHandler, DOIHandler

__version__ = "0.1.0"
__all__ = ['Url2Bibtex', 'Handler', 'HandlerRegistry', 'ArxivHandler', 'OpenReviewHandler', 'SemanticScholarHandler', 'GitHubHandler', 'DOIHandler']
