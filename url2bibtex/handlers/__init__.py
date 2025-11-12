"""Built-in handlers for url2bibtex."""

from .arxiv_handler import ArxivHandler
from .openreview_handler import OpenReviewHandler
from .semanticscholar_handler import SemanticScholarHandler
from .github_handler import GitHubHandler
from .doi_handler import DOIHandler

__all__ = ['ArxivHandler', 'OpenReviewHandler', 'SemanticScholarHandler', 'GitHubHandler', 'DOIHandler']
