"""Base handler class for URL to BibTeX conversion."""

from abc import ABC, abstractmethod
from typing import Optional
import re


class Handler(ABC):
    """
    Abstract base class for URL handlers.

    Each handler should implement:
    - can_handle(): Check if this handler can process the given URL
    - extract_bibtex(): Extract BibTeX entry from the URL
    """

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """
        Check if this handler can process the given URL.

        Args:
            url: The URL to check

        Returns:
            True if this handler can process the URL, False otherwise
        """
        pass

    @abstractmethod
    def extract_bibtex(self, url: str) -> Optional[str]:
        """
        Extract BibTeX entry from the given URL.

        Args:
            url: The URL to extract BibTeX from

        Returns:
            BibTeX entry as a string, or None if extraction failed
        """
        pass


class HandlerRegistry:
    """Registry for managing URL handlers."""

    def __init__(self):
        self._handlers: list[Handler] = []

    def register(self, handler: Handler) -> None:
        """
        Register a new handler.

        Args:
            handler: The handler instance to register
        """
        self._handlers.append(handler)

    def unregister(self, handler: Handler) -> None:
        """
        Unregister a handler.

        Args:
            handler: The handler instance to unregister
        """
        if handler in self._handlers:
            self._handlers.remove(handler)

    def get_handler(self, url: str) -> Optional[Handler]:
        """
        Get the first handler that can process the given URL.

        Args:
            url: The URL to find a handler for

        Returns:
            A handler that can process the URL, or None if no handler found
        """
        for handler in self._handlers:
            if handler.can_handle(url):
                return handler
        return None

    def list_handlers(self) -> list[Handler]:
        """
        Get a list of all registered handlers.

        Returns:
            List of registered handlers
        """
        return self._handlers.copy()
