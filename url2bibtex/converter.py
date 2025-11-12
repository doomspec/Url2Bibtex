"""Main URL to BibTeX converter."""

from typing import Optional
from .handler import HandlerRegistry, Handler


class Url2Bibtex:
    """Main converter class for URL to BibTeX conversion."""

    def __init__(self):
        self.registry = HandlerRegistry()

    def register_handler(self, handler: Handler) -> None:
        """
        Register a custom handler.

        Args:
            handler: The handler instance to register
        """
        self.registry.register(handler)

    def unregister_handler(self, handler: Handler) -> None:
        """
        Unregister a handler.

        Args:
            handler: The handler instance to unregister
        """
        self.registry.unregister(handler)

    def convert(self, url: str) -> Optional[str]:
        """
        Convert a URL to BibTeX entry.

        Args:
            url: The URL to convert

        Returns:
            BibTeX entry as a string, or None if conversion failed

        Raises:
            ValueError: If no handler can process the URL
        """
        handler = self.registry.get_handler(url)
        if handler is None:
            raise ValueError(f"No handler found for URL: {url}")

        return handler.extract_bibtex(url)

    def can_convert(self, url: str) -> bool:
        """
        Check if the URL can be converted.

        Args:
            url: The URL to check

        Returns:
            True if a handler exists for the URL, False otherwise
        """
        return self.registry.get_handler(url) is not None
