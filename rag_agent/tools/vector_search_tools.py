# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Enhanced Vector Database Search Tools for deep policy analysis."""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional

import chromadb
from chromadb.config import Settings
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from google.adk.tools import FunctionTool, ToolContext 


class VectorPolicyManager:
    """Manages vector database for insurance policy documents."""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent.parent
        self.raw_policies_dir = self.root_dir / "data" / "raw_policies"
        self.db_path = self.root_dir / "data" / "vector_db"
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(
                anonymized_telemetry=False,
                is_persistent=True
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="insurance_policies",
            metadata={"description": "Insurance policy documents with enhanced search"}
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  # Smaller chunks for better precision
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        print(f"Vector DB initialized at: {self.db_path}")
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def process_and_index_policies(self) -> Dict[str, Any]:
        """Process raw policy PDFs and index them in vector database."""
        if not self.raw_policies_dir.exists():
            self.raw_policies_dir.mkdir(parents=True, exist_ok=True)
            return {
                "status": "warning",
                "message": f"Created raw_policies directory at {self.raw_policies_dir}. Please add PDF files to index.",
                "indexed_files": []
            }
        
        pdf_files = list(self.raw_policies_dir.glob("*.pdf"))
        if not pdf_files:
            return {
                "status": "warning", 
                "message": "No PDF files found in raw_policies directory.",
                "indexed_files": []
            }
        
        indexed_files = []
        
        for pdf_file in pdf_files:
            print(f"Processing: {pdf_file.name}")
            
            # Extract text from PDF
            text = self.extract_text_from_pdf(pdf_file)
            if not text.strip():
                continue
            
            # Split into chunks
            chunks = self.text_splitter.split_text(text)
            
            # Create document IDs and metadata
            file_hash = hashlib.md5(pdf_file.name.encode()).hexdigest()[:8]
            
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) < 50:  # Skip very small chunks
                    continue
                    
                chunk_id = f"{file_hash}_chunk_{i}"
                
                documents.append(chunk)
                metadatas.append({
                    "source": pdf_file.name,
                    "chunk_index": i,
                    "file_path": str(pdf_file),
                    "chunk_size": len(chunk)
                })
                ids.append(chunk_id)
            
            # Add to vector database
            if documents:
                try:
                    self.collection.add(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids
                    )
                    indexed_files.append({
                        "file": pdf_file.name,
                        "chunks": len(documents),
                        "total_chars": sum(len(doc) for doc in documents)
                    })
                    print(f"✅ Indexed {pdf_file.name}: {len(documents)} chunks")
                except Exception as e:
                    print(f"❌ Error indexing {pdf_file.name}: {e}")
        
        return {
            "status": "success",
            "message": f"Indexed {len(indexed_files)} policy documents.",
            "indexed_files": indexed_files
        }
    
    def vector_search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search using vector embeddings."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            search_results = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    search_results.append({
                        "content": doc,
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else 0.0
                    })
            
            return search_results
        except Exception as e:
            print(f"Vector search error: {e}")
            return []


# Global vector manager instance
vector_manager = None

def get_vector_manager():
    """Get or initialize vector manager."""
    global vector_manager
    if vector_manager is None:
        vector_manager = VectorPolicyManager()
    return vector_manager


def enhanced_search_documents(query: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Enhanced search using vector database for semantic similarity.
    
    Args:
        query: The search query or question.
        tool_context: The tool context (automatically provided by ADK).
    
    Returns:
        A dictionary containing the enhanced search results.
    """
    try:
        vm = get_vector_manager()
        
        # Perform vector search
        vector_results = vm.vector_search(query, n_results=8)
        
        if not vector_results:
            return {
                "status": "not_found",
                "answer": "No information found in the vector database. Try indexing policy documents first.",
                "sources": [],
                "method": "vector_search"
            }
        
        # Enhanced result processing
        def extract_answer_from_results(results: List[Dict], query: str) -> str:
            """Extract the most relevant answer from vector search results."""
            
            # Group results by source for better context
            source_groups = {}
            for result in results:
                source = result['metadata']['source']
                if source not in source_groups:
                    source_groups[source] = []
                source_groups[source].append(result)
            
            # Extract relevant content
            answer_parts = []
            
            # Prioritize results with lower distance (higher similarity)
            sorted_results = sorted(results, key=lambda x: x.get('distance', 1.0))
            
            for result in sorted_results[:5]:  # Top 5 results
                content = result['content']
                
                # For contact queries, prioritize chunks with contact info
                if any(word in query.lower() for word in ['contact', 'phone', 'call', 'reach', 'number']):
                    if any(word in content.lower() for word in ['phone', 'call', 'contact', '0345', 'halifax', 'service']):
                        answer_parts.insert(0, content)  # Prioritize
                    elif any(word in content.lower() for word in ['claim', 'report', 'notify']):
                        answer_parts.append(content)
                else:
                    answer_parts.append(content)
            
            # Clean and join answer parts
            combined_answer = " ".join(answer_parts)
            
            # Limit length but allow more for contact/claim queries  
            max_length = 2000 if any(word in query.lower() for word in ['contact', 'claim', 'phone', 'call']) else 1200
            if len(combined_answer) > max_length:
                combined_answer = combined_answer[:max_length] + "..."
            
            return combined_answer
        
        answer = extract_answer_from_results(vector_results, query)
        sources = list(set(result['metadata']['source'] for result in vector_results))
        
        return {
            "status": "success",
            "answer": answer,
            "sources": sources,
            "method": "vector_search",
            "results_count": len(vector_results),
            "message": f"Found information using semantic search from {len(sources)} document(s)."
        }
        
    except Exception as e:
        return {
            "status": "error",
            "answer": f"Error during enhanced search: {str(e)}",
            "sources": [],
            "method": "vector_search"
        }


def index_policy_documents(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Index policy documents from raw_policies directory into vector database.
    
    Args:
        tool_context: The tool context (automatically provided by ADK).
    
    Returns:
        A dictionary containing indexing results.
    """
    try:
        vm = get_vector_manager()
        result = vm.process_and_index_policies()
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error indexing documents: {str(e)}",
            "indexed_files": []
        }


# Tool definitions
enhanced_search_tool = FunctionTool(enhanced_search_documents)
index_documents_tool = FunctionTool(index_policy_documents)

# Export tools
vector_search_tools = [
    enhanced_search_tool,
    index_documents_tool,
]