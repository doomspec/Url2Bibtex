"""Built-in handlers for url2bibtex."""

from .arxiv_handler import ArxivHandler
from .openreview_handler import OpenReviewHandler
from .semanticscholar_handler import SemanticScholarHandler
from .github_handler import GitHubHandler
from .doi_handler import DOIHandler
from .aclanthology_handler import ACLAnthologyHandler
from .htmlmeta_handler import HTMLMetaHandler
from .ieee_handler import IEEEHandler
from .biorxiv_handler import BioRxivHandler

__all__ = ['ArxivHandler', 'OpenReviewHandler', 'SemanticScholarHandler', 'GitHubHandler', 'DOIHandler', 'ACLAnthologyHandler', 'HTMLMetaHandler', 'IEEEHandler', 'BioRxivHandler']
