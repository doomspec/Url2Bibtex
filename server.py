#!/usr/bin/env python3
"""FastAPI server for URL to BibTeX conversion."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
import uvicorn

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
    CellHandler
)


# Initialize FastAPI app
app = FastAPI(
    title="URL to BibTeX Converter API",
    description="Convert academic paper URLs to BibTeX citations",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize converter with all handlers
converter = Url2Bibtex()
converter.register_handler(ArxivHandler())
converter.register_handler(DOIHandler())
converter.register_handler(BioRxivHandler())
converter.register_handler(PIIHandler())
converter.register_handler(CellHandler())
converter.register_handler(OpenReviewHandler())
converter.register_handler(SemanticScholarHandler())
converter.register_handler(GitHubHandler())
converter.register_handler(IEEEHandler())
converter.register_handler(ACLAnthologyHandler())
converter.register_handler(HTMLMetaHandler())  # Fallback handler last


# Request/Response models
class ConvertRequest(BaseModel):
    url: str = Field(..., description="The URL to convert to BibTeX")

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://arxiv.org/abs/2103.15348"
            }
        }


class ConvertResponse(BaseModel):
    url: str = Field(..., description="The original URL")
    bibtex: str = Field(..., description="The BibTeX citation")
    success: bool = Field(True, description="Whether the conversion was successful")


class ErrorResponse(BaseModel):
    url: str = Field(..., description="The original URL")
    error: str = Field(..., description="Error message")
    success: bool = Field(False, description="Whether the conversion was successful")


class HealthResponse(BaseModel):
    status: str = Field("ok", description="Service health status")
    handlers: int = Field(..., description="Number of registered handlers")


class HandlerInfo(BaseModel):
    name: str = Field(..., description="Handler class name")
    description: str = Field(..., description="Handler description")


class HandlersResponse(BaseModel):
    handlers: List[HandlerInfo] = Field(..., description="List of available handlers")


# API Endpoints
@app.get("/", tags=["General"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "URL to BibTeX Converter API",
        "version": "0.1.0",
        "endpoints": {
            "convert": "/convert",
            "health": "/health",
            "handlers": "/handlers",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health():
    """Health check endpoint."""
    handler_count = len(converter.registry.list_handlers())
    return HealthResponse(status="ok", handlers=handler_count)


@app.get("/handlers", response_model=HandlersResponse, tags=["General"])
async def list_handlers():
    """List all available handlers."""
    handlers = [
        HandlerInfo(name="ArxivHandler", description="ArXiv preprint papers"),
        HandlerInfo(name="BioRxivHandler", description="bioRxiv preprint papers"),
        HandlerInfo(name="OpenReviewHandler", description="OpenReview conference submissions"),
        HandlerInfo(name="SemanticScholarHandler", description="Semantic Scholar academic papers"),
        HandlerInfo(name="GitHubHandler", description="GitHub repositories (CITATION.cff)"),
        HandlerInfo(name="DOIHandler", description="DOI resolution (universal)"),
        HandlerInfo(name="ACLAnthologyHandler", description="ACL Anthology papers"),
        HandlerInfo(name="HTMLMetaHandler", description="Fallback for HTML meta tags (Nature, IEEE, etc.)"),
    ]
    return HandlersResponse(handlers=handlers)


@app.post("/convert", response_model=ConvertResponse, tags=["Conversion"])
async def convert_url(request: ConvertRequest):
    """
    Convert a URL to BibTeX format.

    Supports:
    - ArXiv (https://arxiv.org/abs/...)
    - bioRxiv (https://www.biorxiv.org/content/10.1101/...)
    - OpenReview (https://openreview.net/forum?id=...)
    - Semantic Scholar (https://www.semanticscholar.org/paper/...)
    - GitHub (https://github.com/owner/repo)
    - DOI (https://doi.org/10.xxxx/xxx)
    - ACL Anthology (https://aclanthology.org/...)
    - Any publisher with HTML meta tags (Nature, IEEE, Springer, etc.)
    """
    url = request.url

    # Check if URL can be converted
    if not converter.can_convert(url):
        raise HTTPException(
            status_code=400,
            detail=f"No handler available for URL: {url}"
        )

    try:
        # Convert URL to BibTeX
        bibtex = converter.convert(url)

        if not bibtex:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract BibTeX from URL: {url}"
            )

        return ConvertResponse(
            url=url,
            bibtex=bibtex,
            success=True
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


@app.get("/convert", response_model=ConvertResponse, tags=["Conversion"])
async def convert_url_get(url: str = Query(..., description="The URL to convert to BibTeX")):
    """
    Convert a URL to BibTeX format (GET method).

    Same functionality as POST /convert but using query parameters.
    """
    request = ConvertRequest(url=url)
    return await convert_url(request)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="URL to BibTeX Converter API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    args = parser.parse_args()

    print(f"Starting URL to BibTeX Converter API on {args.host}:{args.port}")
    print(f"API Documentation: http://{args.host}:{args.port}/docs")

    uvicorn.run(
        "server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )
