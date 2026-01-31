from url2bibtex import Url2Bibtex
from url2bibtex.handlers import (
    IEEEHandler,
    ArxivHandler,
    OpenReviewHandler,
    SemanticScholarHandler,
    GitHubHandler,
    DOIHandler,
    ACLAnthologyHandler,
    HTMLMetaHandler,
    BioRxivHandler,
    PIIHandler,
    CellHandler,
    UrlParamHandler
)
default_converter = Url2Bibtex()
default_converter.register_handler(UrlParamHandler())  # Check for bib= parameter first
default_converter.register_handler(ArxivHandler())
default_converter.register_handler(DOIHandler())
default_converter.register_handler(BioRxivHandler())
default_converter.register_handler(PIIHandler())
default_converter.register_handler(CellHandler())
default_converter.register_handler(OpenReviewHandler())
default_converter.register_handler(SemanticScholarHandler())
default_converter.register_handler(GitHubHandler())
default_converter.register_handler(IEEEHandler())
default_converter.register_handler(ACLAnthologyHandler())
default_converter.register_handler(HTMLMetaHandler())  # Fallback handler last