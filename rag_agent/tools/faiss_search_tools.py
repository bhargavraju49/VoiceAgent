"""
FAISS-based vector search implementation for policy documents.
Alternative to ChromaDB that avoids dependency conflicts.
"""

import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from google.adk.tools import FunctionTool, ToolContext

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    print("FAISS not available. Install with: pip install faiss-cpu")
    faiss = None
    FAISS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("Sentence transformers not available. Install with: pip install sentence-transformers")
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    TEXT_SPLITTER_AVAILABLE = True
except ImportError:
    print("LangChain text splitters not available. Install with: pip install langchain-text-splitters")
    RecursiveCharacterTextSplitter = None
    TEXT_SPLITTER_AVAILABLE = False


class FAISSPolicyManager:
    """FAISS-based vector database manager for policy documents"""
    
    def __init__(self):
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS is required but not installed. Run: pip install faiss-cpu")
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("Sentence transformers required. Run: pip install sentence-transformers")
        
        self.root_dir = Path(__file__).parent.parent.parent
        self.raw_policies_dir = self.root_dir / "data" / "raw_policies"
        self.vector_db_path = self.root_dir / "data" / "faiss_db"
        
        # Ensure vector_db directory exists
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize the embedding model
        print("Loading SentenceTransformer model...")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384  # Dimension of all-MiniLM-L6-v2
        
        # Initialize text splitter
        if TEXT_SPLITTER_AVAILABLE:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=100,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
        else:
            self.text_splitter = None
        
        # FAISS index and metadata
        self.index = None
        self.documents = []  # Store document chunks
        self.metadata = []   # Store metadata for each chunk
        
        # Try to load existing index
        self._load_index()
        
    def _load_index(self):
        """Load existing FAISS index if it exists"""
        index_file = self.vector_db_path / "faiss_index.bin"
        docs_file = self.vector_db_path / "documents.pkl"
        meta_file = self.vector_db_path / "metadata.pkl"
        
        if index_file.exists() and docs_file.exists() and meta_file.exists():
            try:
                self.index = faiss.read_index(str(index_file))
                
                with open(docs_file, 'rb') as f:
                    self.documents = pickle.load(f)
                
                with open(meta_file, 'rb') as f:
                    self.metadata = pickle.load(f)
                
                print(f"Loaded existing FAISS index with {len(self.documents)} documents")
            except Exception as e:
                print(f"Error loading existing index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index"""
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.documents = []
        self.metadata = []
        print("Created new FAISS index")
    
    def _save_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            index_file = self.vector_db_path / "faiss_index.bin"
            docs_file = self.vector_db_path / "documents.pkl"
            meta_file = self.vector_db_path / "metadata.pkl"
            
            faiss.write_index(self.index, str(index_file))
            
            with open(docs_file, 'wb') as f:
                pickle.dump(self.documents, f)
            
            with open(meta_file, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            print("FAISS index saved successfully")
        except Exception as e:
            print(f"Error saving FAISS index: {e}")
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks"""
        if self.text_splitter:
            return self.text_splitter.split_text(text)
        else:
            # Simple fallback splitting
            sentences = text.split('. ')
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk + sentence) < 500:
                    current_chunk += sentence + ". "
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + ". "
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            return chunks
    
    def index_documents(self) -> str:
        """Index all documents in the raw_policies directory"""
        if not self.raw_policies_dir.exists():
            return f"Raw policies directory not found: {self.raw_policies_dir}"
        
        # Find all text files
        text_files = list(self.raw_policies_dir.glob("*.txt"))
        json_files = list(self.raw_policies_dir.glob("*.json"))
        
        if not text_files and not json_files:
            return "No .txt or .json files found in raw_policies directory"
        
        all_chunks = []
        all_embeddings = []
        all_metadata = []
        
        # Process text files
        for txt_file in text_files:
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                chunks = self._split_text(content)
                print(f"Processing {txt_file.name}: {len(chunks)} chunks")
                
                for i, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    all_metadata.append({
                        'source': txt_file.name,
                        'chunk_id': i,
                        'type': 'text'
                    })
                
            except Exception as e:
                print(f"Error processing {txt_file.name}: {e}")
        
        # Process JSON files
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert JSON to text representation
                if isinstance(data, dict):
                    content = json.dumps(data, indent=2)
                elif isinstance(data, list):
                    content = "\n".join([json.dumps(item, indent=2) for item in data])
                else:
                    content = str(data)
                
                chunks = self._split_text(content)
                print(f"Processing {json_file.name}: {len(chunks)} chunks")
                
                for i, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    all_metadata.append({
                        'source': json_file.name,
                        'chunk_id': i,
                        'type': 'json'
                    })
                
            except Exception as e:
                print(f"Error processing {json_file.name}: {e}")
        
        if not all_chunks:
            return "No content found to index"
        
        # Generate embeddings
        print(f"Generating embeddings for {len(all_chunks)} chunks...")
        embeddings = self.embedder.encode(all_chunks, convert_to_numpy=True)
        
        # Clear existing index
        self._create_new_index()
        
        # Add embeddings to FAISS index
        self.index.add(embeddings.astype('float32'))
        self.documents = all_chunks
        self.metadata = all_metadata
        
        # Save index
        self._save_index()
        
        return f"Successfully indexed {len(all_chunks)} chunks from {len(text_files + json_files)} files"
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents using semantic similarity"""
        if self.index is None or len(self.documents) == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.embedder.encode([query], convert_to_numpy=True)
        
        # Search FAISS index
        distances, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx >= len(self.documents):
                continue
                
            results.append({
                'content': self.documents[idx],
                'metadata': self.metadata[idx],
                'score': float(1.0 / (1.0 + distance)),  # Convert distance to similarity score
                'rank': i + 1
            })
        
        return results


# Create global instance
_faiss_manager = None

def get_faiss_manager():
    """Get or create FAISS manager instance"""
    global _faiss_manager
    if _faiss_manager is None:
        _faiss_manager = FAISSPolicyManager()
    return _faiss_manager


def faiss_search_documents_impl(query: str, max_results: int = 5, tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Search policy documents using FAISS vector similarity.
    
    Args:
        query: The search query (natural language)
        max_results: Maximum number of results to return (default 5)
        tool_context: The tool context (automatically provided by ADK)
    
    Returns:
        Dictionary containing search results
    """
    import logging
    try:
        manager = get_faiss_manager()
        results = manager.search_documents(query, max_results)

        if not results:
            logging.info(f"[FAISS SEARCH] No relevant documents found for query: {query}")
            return {
                "status": "no_results",
                "message": f"No relevant documents found for: {query}",
                "query": query,
                "results": []
            }

        formatted_results = []
        response_text = ""

        logging.info(f"[FAISS SEARCH] Query: {query}")
        for idx, result in enumerate(results):
            content = result['content']
            metadata = result['metadata']
            score = result['score']

            # Truncate long content
            if len(content) > 500:
                content = content[:500] + "..."

            formatted_result = {
                "content": content,
                "source": metadata['source'],
                "score": score,
                "type": metadata['type']
            }
            formatted_results.append(formatted_result)

            logging.info(f"[FAISS SEARCH] Result {idx+1}: Score={score}, Source={metadata['source']}, Content Preview={content[:120].replace('\n',' ')}")
            response_text += f"{content}\n\n"

        return {
            "status": "success",
            "message": response_text.strip(),
            "query": query,
            "results": formatted_results
        }

    except Exception as e:
        logging.exception(f"[FAISS SEARCH] Error searching documents for query: {query}")
        return {
            "status": "error",
            "message": f"Error searching documents: {str(e)}",
            "query": query,
            "results": []
        }


def faiss_index_documents_impl(tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Index all policy documents in the raw_policies directory using FAISS.
    
    Args:
        tool_context: The tool context (automatically provided by ADK)
    
    Returns:
        Dictionary containing indexing status
    """
    try:
        manager = get_faiss_manager()
        result = manager.index_documents()
        return {
            "status": "success",
            "message": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error indexing documents: {str(e)}"
        }


# Create FunctionTool instances
faiss_search_documents = FunctionTool(faiss_search_documents_impl)
faiss_index_documents = FunctionTool(faiss_index_documents_impl)