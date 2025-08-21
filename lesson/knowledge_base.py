# knowledge_base.py
import os
import requests
from pypdf import PdfReader
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
import streamlit as st
from typing import List, Dict
import hashlib

class ClimateKnowledgeBase:
    """
    A comprehensive document processing system for climate information.
    Handles PDFs, web articles, and provides intelligent text chunking.
    """

    def __init__(self):
        self.documents = []  # Store all processed document chunks

        # Configure text splitter for optimal chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,        # ~250 words per chunk (good for AI context)
            chunk_overlap=200,      # Overlap to maintain context between chunks
            length_function=len,    # Use character count
        )

    def load_pdf(self, file_path: str, source_name: str = None) -> List[Dict]:
        """
        Load and process a PDF file into searchable chunks.

        Args:
            file_path: Path to the PDF file
            source_name: Human-readable name for the document

        Returns:
            List of document chunks with metadata
        """
        try:
            if source_name is None:
                source_name = os.path.basename(file_path)

            # Extract text using pypdf
            reader = PdfReader(file_path)
            full_text = ""

            # Combine all pages into one text block
            for page in reader.pages:
                full_text += page.extract_text() + "\n"

            # Split into manageable chunks using LangChain
            chunks = self.text_splitter.split_text(full_text)

            # Create structured document objects
            documents = []
            for i, chunk in enumerate(chunks):
                doc = {
                    "content": chunk,
                    "source": source_name,
                    "source_type": "PDF",
                    "chunk_id": f"{source_name}_chunk_{i}",
                    "page_count": len(reader.pages)
                }
                documents.append(doc)

            # Add to knowledge base
            self.documents.extend(documents)
            return documents

        except Exception as e:
            st.error(f"Error loading PDF {file_path}: {e}")
            return []

    def load_web_article(self, url: str, source_name: str = None) -> List[Dict]:
        """
        Fetch and process a web article into searchable chunks.

        Args:
            url: Web URL to fetch
            source_name: Human-readable name for the source

        Returns:
            List of document chunks with metadata
        """
        try:
            if source_name is None:
                source_name = url.split("//")[1].split("/")[0]  # Extract domain

            # Fetch webpage with proper headers (avoid bot detection)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse HTML and clean content
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove unwanted elements (navigation, ads, etc.)
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()

            # Extract clean text content
            text = soup.get_text()

            # Clean up whitespace and empty lines
            lines = [line.strip() for line in text.splitlines()]
            text = ' '.join([line for line in lines if line])

            # Split into chunks using LangChain
            chunks = self.text_splitter.split_text(text)

            # Create structured document objects
            documents = []
            for i, chunk in enumerate(chunks):
                doc = {
                    "content": chunk,
                    "source": source_name,
                    "source_type": "Web Article",
                    "url": url,
                    "chunk_id": f"{source_name}_chunk_{i}"
                }
                documents.append(doc)

            # Add to knowledge base
            self.documents.extend(documents)
            return documents

        except Exception as e:
            st.error(f"Error loading web article {url}: {e}")
            return []

    def search_documents(self, query: str, max_results: int = 3) -> List[Dict]:
        """
        Search through loaded documents for relevant content.
        Uses simple keyword matching (we'll upgrade to semantic search in Day 4).

        Args:
            query: User's question or search terms
            max_results: Maximum number of chunks to return

        Returns:
            List of relevant document chunks, sorted by relevance
        """
        query_lower = query.lower()
        scored_docs = []

        for doc in self.documents:
            content_lower = doc["content"].lower()

            # Simple scoring based on keyword frequency
            score = 0
            query_words = query_lower.split()

            for word in query_words:
                if len(word) > 3:  # Only count meaningful words
                    score += content_lower.count(word)

            if score > 0:
                doc_copy = doc.copy()
                doc_copy["relevance_score"] = score
                scored_docs.append(doc_copy)

        # Sort by relevance and return top results
        scored_docs.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_docs[:max_results]

    def get_document_stats(self) -> Dict:
        """Get statistics about the current knowledge base"""
        if not self.documents:
            return {"total_chunks": 0, "sources": 0, "types": []}

        sources = set(doc["source"] for doc in self.documents)
        types = set(doc["source_type"] for doc in self.documents)

        return {
            "total_chunks": len(self.documents),
            "sources": len(sources),
            "source_list": list(sources),
            "types": list(types)
        }

# Curated list of reliable climate information sources
CLIMATE_SOURCES = {
    "IPCC AR6 Summary": "https://www.ipcc.ch/report/ar6/wg1/downloads/report/IPCC_AR6_WGI_SPM.pdf",
    "NASA Climate Change": "https://climate.nasa.gov/what-is-climate-change/",
    "EPA Climate Indicators": "https://www.epa.gov/climate-indicators",
    "NOAA Climate Science": "https://www.climate.gov/news-features/understanding-climate/climate-change-snow-and-ice",
    "IEA Energy Transition": "https://www.iea.org/topics/energy-transitions"
}