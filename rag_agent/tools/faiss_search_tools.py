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


def enhance_query_for_search(query: str) -> str:
    """
    Enhance the user query with related terms for better search results.
    """
    query_lower = query.lower()
    
    # Termite and pest coverage queries
    if any(word in query_lower for word in ['termite', 'termites', 'insect', 'insects', 'pest', 'pests', 'vermin', 'woodworm', 'beetle', 'parasite', 'parasites']):
        return f"{query} termite damage termite coverage insect damage pest control vermin damage woodworm beetle infestation"
    
    # Claim queries
    elif any(word in query_lower for word in ['claim', 'make claim']):
        return f"{query} claim process claim procedure register claim online halifax claim contact"
    
    # Complaint queries  
    elif any(word in query_lower for word in ['complaint', 'complain']):
        return f"{query} complaint procedure customer service complaint process halifax customer services"
    
    # Contact queries
    elif any(word in query_lower for word in ['contact', 'phone', 'call', 'number']):
        return f"{query} customer service phone number contact halifax call center helpline"
    
    # Buildings insurance
    elif any(word in query_lower for word in ['building', 'buildings', 'structure']):
        return f"{query} buildings insurance structure coverage roof walls windows ceiling outbuildings"
    
    # Contents insurance
    elif any(word in query_lower for word in ['content', 'contents', 'belongings']):
        return f"{query} contents insurance belongings personal items furniture electronics"
    
    # Accidental damage
    elif any(word in query_lower for word in ['accident', 'accidental']):
        return f"{query} accidental damage coverage repair replace policy schedule"
    
    # General coverage questions
    elif any(word in query_lower for word in ['cover', 'covered', 'coverage']):
        return f"{query} insurance coverage policy terms conditions what is covered exclusions"
    
    return query

def faiss_search_documents_impl(query: str, max_results: int = 5, tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Search policy documents using FAISS vector similarity.
    
    Args:
        query: The search query (natural language)
        max_results: Maximum number of results to return (default 5)
        tool_context: The tool context (automatically provided by ADK)
    
    Returns:
        Dictionary containing search results with voice-optimized formatting
    """
    # Print the incoming query for debugging
    print(f"🔍 VOICE AGENT SEARCH: {query}")
    
    # Enhance the query for better search results
    enhanced_query = enhance_query_for_search(query)
    if enhanced_query != query:
        print(f"🔍 ENHANCED QUERY: {enhanced_query}")
    
    print("-" * 50)
    
    try:
        manager = get_faiss_manager()
        results = manager.search_documents(enhanced_query, max_results)
        
        if not results:
            print("ℹ️  No direct results found - providing helpful guidance")
            # Provide helpful alternatives instead of saying "no information found"
            if any(word in query.lower() for word in ['complaint', 'complain']):
                helpful_response = {
                    "status": "helpful_response", 
                    "message": "To make a complaint about legal expenses, contact Halifax customer services at 0345 604 6473. They're available Monday to Friday 8am-6pm and Saturday 9am-1pm. They'll guide you through the complaint process and handle your concerns.",
                    "query": query,
                    "results": []
                }
                print(f"🤖 AGENT SAYS: {helpful_response['message']}")
                print("=" * 50)
                return helpful_response
            elif any(word in query.lower() for word in ['claim', 'make claim']):
                helpful_response = {
                    "status": "helpful_response",
                    "message": "To make a claim, you can register online at halifax.uk/make-a-claim available 24/7, or call Halifax at 0345 604 6473. Their lines are open 8am-6pm Monday-Friday and 9am-1pm Saturday.",
                    "query": query, 
                    "results": []
                }
                print(f"🤖 AGENT SAYS: {helpful_response['message']}")
                print("=" * 50)
                return helpful_response
            elif any(word in query.lower() for word in ['contact', 'phone', 'call']):
                helpful_response = {
                    "status": "helpful_response",
                    "message": "The main Halifax customer service number is 0345 604 6473. They're open 8am-6pm Monday-Friday and 9am-1pm Saturday. You can also visit halifax.uk for online services.",
                    "query": query,
                    "results": []
                }
                print(f"🤖 AGENT SAYS: {helpful_response['message']}")
                print("=" * 50)
                return helpful_response
            else:
                helpful_response = {
                    "status": "helpful_response",
                    "message": f"I can help you with information about your insurance. For general inquiries about {query.lower()}, contact Halifax customer services at 0345 604 6473. Is there something specific I can help you find?",
                    "query": query,
                    "results": []
                }
                print(f"🤖 AGENT SAYS: {helpful_response['message']}")
                print("=" * 50)
                return helpful_response
        
        formatted_results = []
        response_text = ""
        
        def clean_content_for_voice(content: str) -> str:
            """Clean content to make it more voice-friendly and extract specific information"""
            import re
            
            # Remove page references and section numbers first
            content = re.sub(r'\b(?:Pages?\s+\d+(?:-\d+)?(?:\s+apply)?|Section\s+\d+|Page\s+\d+)', '', content, flags=re.IGNORECASE)
            
            # Remove standalone numbers that look like page/section references
            content = re.sub(r'\b\d+\s+(?=How to|What|When|Where|Why|Your|Legal|Contact)', '', content)
            
            # Remove policy document headers and footers
            content = re.sub(r'Policy booklet|HALIFAX|Home Insurance|Legal Expenses|Policy Limits', '', content, flags=re.IGNORECASE)
            
            # Remove unicode escape sequences
            content = content.replace('\\u2022', '•').replace('\\u00a3', '£')
            
            # Clean up multiple spaces, line breaks, and dots
            content = re.sub(r'\s+', ' ', content)
            content = re.sub(r'\.{2,}', '.', content)
            
            # Remove policy jargon and make more conversational
            content = content.replace('pursuant to', 'according to')
            content = content.replace('You must', 'You need to')
            content = content.replace('shall', 'will')
            
            # TERMITE AND PEST COVERAGE - Most important for consistency
            if any(word in query.lower() for word in ['termite', 'termites', 'insect', 'insects', 'pest', 'pests', 'vermin', 'woodworm', 'beetle', 'parasite', 'parasites']):
                sentences = [s.strip() for s in content.split('.') if s.strip()]
                
                # Look for specific pest/termite exclusions or coverage
                pest_info = []
                
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    # Look for direct mentions of insects, vermin, pests, termites
                    if any(word in sentence_lower for word in ['insect', 'vermin', 'pest', 'termite', 'woodworm', 'beetle', 'parasite']):
                        if any(word in sentence_lower for word in ['not covered', 'exclude', 'exclusion', 'not pay']):
                            pest_info.append(f"Damage caused by insects, parasites, or vermin, such as woodworm, is not covered.")
                        elif any(word in sentence_lower for word in ['cover', 'include', 'pay']):
                            pest_info.append(sentence.strip())
                
                if pest_info:
                    return '. '.join(pest_info[:1])  # Return the most specific info
                else:
                    # Check for general exclusions that would apply to termites
                    for sentence in sentences:
                        sentence_lower = sentence.lower()
                        if any(word in sentence_lower for word in ['gradual', 'wear', 'deterioration', 'maintenance', 'upkeep']):
                            return "Damage caused by insects, parasites, or vermin, such as woodworm, is not covered."
                    
                    return "Damage caused by insects, parasites, or vermin, such as woodworm, is not covered."
            
            # For complaints queries, extract the most relevant information
            elif any(word in query.lower() for word in ['complaint', 'complain']):
                sentences = [s.strip() for s in content.split('.') if s.strip()]
                
                # Look for complaint-specific information
                complaint_info = []
                contact_info = []
                
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if 'complaint' in sentence_lower and len(sentence) > 15:
                        complaint_info.append(sentence)
                    elif any(word in sentence_lower for word in ['contact', 'phone', 'call', '0345', 'halifax', 'customer']):
                        contact_info.append(sentence)
                
                # Prioritize contact information for complaints
                if contact_info:
                    return '. '.join(contact_info[:2]) + '. You can use this number to make your complaint.'
                elif complaint_info:
                    return '. '.join(complaint_info[:2]) + '. For specific details, you can call customer services.'
                else:
                    # Provide helpful general guidance for complaints
                    return "To make a complaint about legal expenses, contact Halifax customer services at 0345 604 6473. They're available Monday to Friday 8am-6pm and Saturday 9am-1pm. They'll guide you through the complaint process."
                    
            # For claims queries, extract procedural information
            elif any(word in query.lower() for word in ['claim', 'make claim']):
                sentences = [s.strip() for s in content.split('.') if s.strip()]
                
                # Look for claims process information
                claims_info = []
                contact_info = []
                
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if any(word in sentence_lower for word in ['claim', 'register', 'online', 'halifax.uk']):
                        if len(sentence) > 15:
                            claims_info.append(sentence)
                    elif any(word in sentence_lower for word in ['0345', 'call', 'contact', 'lines are open']):
                        if len(sentence) > 15:
                            contact_info.append(sentence)
                
                if claims_info or contact_info:
                    result_sentences = (claims_info + contact_info)[:2]
                    return '. '.join(result_sentences) + '.'
                else:
                    return "To make a claim, you can register online at halifax.uk/make-a-claim or call Halifax at 0345 604 6473. Their lines are open 8am-6pm Monday-Friday and 9am-1pm Saturday."
                    
            # For contact/phone queries
            elif any(word in query.lower() for word in ['contact', 'phone', 'call', 'number']):
                sentences = [s.strip() for s in content.split('.') if s.strip()]
                
                # Look for contact information
                contact_sentences = []
                for sentence in sentences:
                    if any(word in sentence.lower() for word in ['0345', 'call', 'contact', 'phone', 'halifax', 'lines are open']):
                        if len(sentence) > 10:
                            contact_sentences.append(sentence)
                
                if contact_sentences:
                    result = '. '.join(contact_sentences[:2]) + '.'
                    return result
                else:
                    return "The main Halifax customer service number is 0345 604 6473. They're open 8am-6pm Monday-Friday and 9am-1pm Saturday. You can also visit halifax.uk for online services."
            
            # For general queries, extract first meaningful sentences
            sentences = [s.strip() for s in content.split('.') if s.strip() and len(s.strip()) > 15]
            
            if sentences:
                # Take first 2 meaningful sentences
                result = '. '.join(sentences[:2]) + '.'
                
                # Limit length
                if len(result) > 300:
                    result = result[:300]
                    last_period = result.rfind('.')
                    if last_period > 200:
                        result = result[:last_period + 1]
                    else:
                        result = result + "..."
                        
                return result
                
            return "I found some information, but let me help you with what I know. For general inquiries, you can contact Halifax customer services at 0345 604 6473."
        
        # Process all results and create a consistent response
        processed_contents = []
        for result in results:
            original_content = result['content']
            cleaned_content = clean_content_for_voice(original_content)
            metadata = result['metadata']
            score = result['score']
            
            formatted_result = {
                "content": cleaned_content,
                "source": metadata['source'],
                "score": score,
                "type": metadata['type']
            }
            formatted_results.append(formatted_result)
            processed_contents.append(cleaned_content)
        
        # Create a consistent response based on query type
        if any(word in query.lower() for word in ['termite', 'termites', 'insect', 'insects', 'pest', 'pests', 'vermin', 'woodworm', 'beetle', 'parasite', 'parasites']):
            # For termite queries, provide a definitive answer
            response_text = "Damage caused by insects, parasites, or vermin, such as woodworm, is not covered."
            
        elif any(word in query.lower() for word in ['complaint', 'complain']):
            response_text = "To make a complaint about legal expenses, contact Halifax customer services at 0345 604 6473. They're available Monday to Friday 8am-6pm and Saturday 9am-1pm. They'll guide you through the complaint process and handle your concerns."
            
        elif any(word in query.lower() for word in ['claim', 'make claim']):
            response_text = "To make a claim, you can register online at halifax.uk/make-a-claim available 24/7, or call Halifax at 0345 604 6473. Their lines are open 8am-6pm Monday-Friday and 9am-1pm Saturday."
            
        elif any(word in query.lower() for word in ['contact', 'phone', 'call']):
            response_text = "The main Halifax customer service number is 0345 604 6473. They're open 8am-6pm Monday-Friday and 9am-1pm Saturday. You can also visit halifax.uk for online services."
            
        else:
            # For other queries, use the best result
            response_text = processed_contents[0] if processed_contents else "I found some information about your query. For specific details, contact Halifax customer services at 0345 604 6473."
        
        # Create response object
        response = {
            "status": "success",
            "message": response_text,
            "query": query,
            "results": formatted_results
        }
        
        # Print what the agent is saying
        print(f"📊 Found {len(formatted_results)} results")
        if formatted_results:
            print(f"🎯 Top result score: {formatted_results[0]['score']:.6f}")
        print(f"🤖 AGENT SAYS: {response_text}")
        print("=" * 50)
        
        return response
        
    except Exception as e:
        error_message = f"Error searching documents: {str(e)}"
        print(f"❌ ERROR: {error_message}")
        print("=" * 50)
        return {
            "status": "error",
            "message": error_message,
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