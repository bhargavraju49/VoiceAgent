# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Main entry point for the RAG agent.

This script performs the following steps:
1.  Sets up the environment and logging.
2.  Performs incremental indexing of policy documents.
3.  Initializes the RAG agent with specialized sub-agents.
4.  Starts the ADK service to make the agent available.
"""

import asyncio
import json
import logging
import os
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from rag_agent.agent import create_file_manager_agent, create_search_assistant_agent
from rag_agent.agents.voice_assistant import create_voice_assistant_agent
from rag_agent.orchestrator import RAGOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define paths for data directories
ROOT_DIR = Path(__file__).parent
RAW_POLICIES_DIR = ROOT_DIR / "data" / "raw_policies"
INDEXED_POLICIES_DIR = ROOT_DIR / "data" / "indexed_policies"
FILE_STORE_CONFIG = ROOT_DIR / "file_store_config.json"


def get_file_store_config() -> dict:
    """Load the file store configuration."""
    if FILE_STORE_CONFIG.exists():
        with open(FILE_STORE_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def update_file_store_config(config: dict) -> None:
    """Update the file store configuration."""
    with open(FILE_STORE_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


async def index_new_policies(file_manager_agent: LlmAgent) -> None:
    """
    Index new policy documents from the raw_policies directory.

    This function checks for documents in `raw_policies` that haven't been
    indexed yet, processes them using the file_manager_agent, and stores
    the indexed output in `indexed_policies`.
    """
    logger.info("Starting policy indexing process...")
    
    # Ensure directories exist
    RAW_POLICIES_DIR.mkdir(parents=True, exist_ok=True)
    INDEXED_POLICIES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get the list of already indexed files
    file_store_config = get_file_store_config()
    indexed_files = file_store_config.get("indexed_files", [])
    
    # Get the list of raw policy files (including PDF and Excel files for processing)
    raw_files = [f.name for f in RAW_POLICIES_DIR.iterdir() 
                 if f.is_file() and f.suffix.lower() in ['.txt', '.json', '.md', '.pdf', '.xlsx', '.xls']]
    
    # Determine which files are new
    new_files_to_index = [f for f in raw_files if f not in indexed_files]
    
    if not new_files_to_index:
        logger.info("No new policies to index.")
        return
        
    logger.info(f"Found {len(new_files_to_index)} new policies to index: {new_files_to_index}")
    
    # Get the file processing tool from the agent
    file_processing_tool = None
    for tool in file_manager_agent.tools:
        if tool.func.__name__ == "process_file_for_indexing":
            file_processing_tool = tool
            break
    
    if not file_processing_tool:
        logger.error("Could not find the 'process_file_for_indexing' tool in the file manager agent.")
        # Proceed with simple indexing instead
        logger.info("Proceeding with simple dummy indexing...")

    # Index each new file
    for filename in new_files_to_index:
        raw_file_path = RAW_POLICIES_DIR / filename
        indexed_file_path = INDEXED_POLICIES_DIR / f"{raw_file_path.stem}.json"
        
        logger.info(f"Indexing {raw_file_path}...")
        
        try:
            # Use Gemini API to extract and analyze the document content
            extracted_text = ""
            if raw_file_path.suffix.lower() in ['.xlsx', '.xls']:
                try:
                    import pandas as pd
                    import io
                    
                    logger.info(f"Processing Excel file: {filename}")
                    
                    # Read all sheets from the Excel file
                    excel_data = pd.read_excel(raw_file_path, sheet_name=None)
                    
                    extracted_parts = []
                    for sheet_name, df in excel_data.items():
                        if not df.empty:
                            # Convert DataFrame to readable text format
                            sheet_text = f"\n--- Sheet: {sheet_name} ---\n"
                            
                            # Include column headers
                            sheet_text += f"Columns: {', '.join(df.columns.astype(str))}\n\n"
                            
                            # Convert each row to text
                            for idx, row in df.iterrows():
                                row_text = []
                                for col, val in row.items():
                                    if pd.notna(val) and str(val).strip():
                                        row_text.append(f"{col}: {val}")
                                
                                if row_text:
                                    sheet_text += " | ".join(row_text) + "\n"
                            
                            extracted_parts.append(sheet_text)
                    
                    extracted_text = "\n".join(extracted_parts)
                    logger.info(f"Successfully extracted {len(extracted_text)} characters from Excel file")
                    
                except Exception as e:
                    logger.error(f"Excel processing failed for {filename}: {e}")
                    extracted_text = f"Excel processing error for {filename}: {str(e)}"
                    
            elif raw_file_path.suffix.lower() == '.pdf':
                try:
                    import base64
                    import google.generativeai as genai
                    import os
                    from pathlib import Path
                    
                    # Try to load API key from multiple sources
                    api_key = os.getenv('GOOGLE_API_KEY')
                    
                    # If not in environment, try to load from .env file
                    if not api_key:
                        env_file = Path(__file__).parent / '.env'
                        if env_file.exists():
                            with open(env_file, 'r') as f:
                                for line in f:
                                    if line.startswith('GOOGLE_API_KEY='):
                                        api_key = line.split('=', 1)[1].strip()
                                        # Remove quotes if present
                                        if api_key.startswith('"') and api_key.endswith('"'):
                                            api_key = api_key[1:-1]
                                        elif api_key.startswith("'") and api_key.endswith("'"):
                                            api_key = api_key[1:-1]
                                        break
                    
                    if not api_key:
                        logger.error("GOOGLE_API_KEY not found. Please set it in .env file or environment variables")
                        extracted_text = f"Error: GOOGLE_API_KEY not configured for {filename}"
                    else:
                        genai.configure(api_key=api_key)
                        logger.info(f"Using API key: {api_key[:10]}...")  # Show first 10 chars for verification
                        
                        # Read PDF file as bytes
                        with open(raw_file_path, "rb") as f:
                            pdf_data = f.read()
                        
                        # Create a simple prompt for raw text extraction only
                        extraction_prompt = f"""Extract ALL text content from this PDF document. 
                        
                        DO NOT SUMMARIZE. DO NOT ANALYZE. DO NOT SKIP ANYTHING.
                        
                        Simply extract every single word, definition, clause, section, and paragraph exactly as written in the document.
                        
                        Include:
                        - All definitions sections
                        - All terms and conditions  
                        - All contact information
                        - All coverage details
                        - All exclusions
                        - All procedural information
                        - All fine print
                        - ALL TEXT without any interpretation
                        
                        Return the complete raw text content only."""

                        # Use Gemini to analyze the PDF
                        # Try the latest available models that support file uploads
                        model_names = [
                            'models/gemini-2.5-pro',
                            'models/gemini-2.5-flash', 
                            'models/gemini-2.0-flash-exp',
                            'models/gemini-2.0-flash',
                            'models/gemini-2.0-flash-001'
                        ]
                        
                        response = None
                        model_used = None
                        
                        for model_name in model_names:
                            try:
                                logger.info(f"Trying model: {model_name}")
                                model = genai.GenerativeModel(model_name)
                                
                                response = model.generate_content([
                                    extraction_prompt,
                                    {
                                        "mime_type": "application/pdf",
                                        "data": pdf_data
                                    }
                                ])
                                
                                if response and response.text:
                                    model_used = model_name
                                    logger.info(f"Successfully used model: {model_name}")
                                    break
                                    
                            except Exception as model_error:
                                logger.warning(f"Model {model_name} failed: {model_error}")
                                continue
                        
                        if response and response.text:
                            extracted_text = response.text
                            logger.info(f"Successfully extracted {len(extracted_text)} characters using {model_used}")
                        else:
                            # If all models fail, try to list available models for debugging
                            try:
                                available_models = list(genai.list_models())
                                model_list = [m.name for m in available_models if 'generateContent' in m.supported_generation_methods]
                                logger.info(f"Available models for generateContent: {model_list}")
                                extracted_text = f"No working model found for {filename}. Available models: {', '.join(model_list[:5])}"
                            except Exception as list_error:
                                logger.error(f"Could not list models: {list_error}")
                                extracted_text = f"Gemini API failed for {filename} - no working model found"
                            
                except Exception as e:
                    logger.error(f"Gemini API extraction failed for {filename}: {e}")
                    extracted_text = f"Gemini API extraction error for {filename}: {str(e)}"
            else:
                # For non-PDF files, try to read as text
                try:
                    with open(raw_file_path, "r", encoding="utf-8") as f:
                        extracted_text = f.read()
                except Exception as e:
                    logger.warning(f"Could not read {filename} as text: {e}")
                    extracted_text = f"Content from {filename} - text extraction failed"

            # Split the raw text into proper chunks with sliding windows
            chunks = []
            if extracted_text.strip():
                # Clean the text first
                text = extracted_text.strip()
                
                # Split into words for proper chunking
                words = text.split()
                chunk_size = 800  # words per chunk
                overlap = 100     # overlapping words between chunks
                
                for i in range(0, len(words), chunk_size - overlap):
                    chunk_words = words[i:i + chunk_size]
                    chunk_text = " ".join(chunk_words)
                    
                    # Only add meaningful chunks (not too short)
                    if len(chunk_text.strip()) > 100:
                        chunks.append(chunk_text.strip())
                    
                    # Stop if we've reached the end
                    if i + chunk_size >= len(words):
                        break
                
                logger.info(f"Created {len(chunks)} overlapping chunks from raw text")
            
            if not chunks:
                chunks = [extracted_text] if extracted_text.strip() else [f"No content extracted from {filename}"]

            # Create the index file with raw text chunks
            index_content = {
                "source_filename": filename,
                "content_summary": f"Raw text extraction from {filename} - {len(chunks)} chunks with overlapping windows",
                "chunks": chunks
            }
            with open(indexed_file_path, "w", encoding="utf-8") as f:
                json.dump(index_content, f, indent=2)

            logger.info(f"Successfully indexed {filename} to {indexed_file_path}")
            
            # Update the list of indexed files
            indexed_files.append(filename)
            
        except Exception as e:
            logger.error(f"Failed to index {filename}: {e}")

    # Update the file store config with the new list of indexed files
    file_store_config["indexed_files"] = indexed_files
    update_file_store_config(file_store_config)
    
    logger.info("Policy indexing process complete.")


async def main() -> None:
    """Initialize and run the RAG agent."""
    
    # 1. Create the sub-agents (without LLM to avoid API key validation)
    # These agents are specialized for insurance policies
    file_manager_agent = create_file_manager_agent(None)
    search_assistant_agent = create_search_assistant_agent(None)
    voice_assistant_agent = create_voice_assistant_agent(None)
    
    # 2. Perform startup indexing (only text files to avoid API key issues)
    await index_new_policies(file_manager_agent)
    
    # 3. Create the main orchestrator agent
    orchestrator = RAGOrchestrator(
        name="InsurancePolicyRAGOrchestrator",
        policy_manager=file_manager_agent,
        search_assistant=search_assistant_agent,
        voice_assistant=voice_assistant_agent,
    )
    
    # 4. Agent is ready - use ADK CLI to start
    print("\n✅ Insurance Policy RAG Agent is ready!")
    print("To start the agent, run: adk web")
    print("Then go to http://localhost:8000 and select 'InsurancePolicyRAGOrchestrator'")
    
    return orchestrator


if __name__ == "__main__":
    asyncio.run(main())
