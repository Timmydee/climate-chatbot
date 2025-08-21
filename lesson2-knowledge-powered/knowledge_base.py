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
    def __init__(self):
        self.documents = []
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
    
    def load_pdf(self, file_path: str, source_name: str = None) -> List[Dict]:
        """Load and process a PDF file"""
        try:
            if source_name is None:
                source_name = os.path.basename(file_path)
            
            # Read PDF
            reader = PdfReader(file_path)
            full_text = ""
            
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
            
            # Split into chunks
            chunks = self.text_splitter.split_text(full_text)
            
            # Create document objects
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
            
            self.documents.extend(documents)
            return documents
            
        except Exception as e:
            st.error(f"Error loading PDF {file_path}: {e}")
            return []
    
    def load_web_article(self, url: str, source_name: str = None) -> List[Dict]:
        """Load and process a web article"""
        try:
            if source_name is None:
                source_name = url.split("//")[1].split("/")[0]  # Extract domain
            
            # Fetch webpage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Extract text content
            text = soup.get_text()
            
            # Clean up text
            lines = [line.strip() for line in text.splitlines()]
            text = ' '.join([line for line in lines if line])
            
            # Split into chunks
            chunks = self.text_splitter.split_text(text)
            
            # Create document objects
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
            
            self.documents.extend(documents)
            return documents
            
        except Exception as e:
            st.error(f"Error loading web article {url}: {e}")
            return []
    
    def search_documents(self, query: str, max_results: int = 3) -> List[Dict]:
        """Simple keyword search through documents"""
        query_lower = query.lower()
        scored_docs = []
        
        for doc in self.documents:
            content_lower = doc["content"].lower()
            
            # Simple scoring based on keyword matches
            score = 0
            query_words = query_lower.split()
            
            for word in query_words:
                if len(word) > 3:  # Only count longer words
                    score += content_lower.count(word)
            
            if score > 0:
                doc_copy = doc.copy()
                doc_copy["relevance_score"] = score
                scored_docs.append(doc_copy)
        
        # Sort by relevance and return top results
        scored_docs.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_docs[:max_results]
    
    def get_document_stats(self) -> Dict:
        """Get statistics about loaded documents"""
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

# Predefined climate knowledge sources
CLIMATE_SOURCES = {
    "IPCC AR6 Summary": "https://www.ipcc.ch/report/ar6/wg1/downloads/report/IPCC_AR6_WGI_SPM.pdf",
    "NASA Climate Change": "https://climate.nasa.gov/what-is-climate-change/",
    "EPA Climate Indicators": "https://www.epa.gov/climate-indicators",
    "NOAA Climate Science": "https://www.climate.gov/news-features/understanding-climate/climate-change-snow-and-ice",
    "IEA Energy Transition": "https://www.iea.org/topics/energy-transitions"
}