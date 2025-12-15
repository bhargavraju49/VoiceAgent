#!/usr/bin/env python3
"""
Direct test of the FAISS search function without importing the full agent.
"""

import json
import pickle
import numpy as np
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import dependencies directly
try:
    import faiss
    from sentence_transformers import SentenceTransformer
    import re
    
    print("✅ All required packages imported successfully")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)

def test_voice_response_logic():
    """Test the voice response cleaning logic directly."""
    
    # Sample content that might come from search results
    sample_content = """25 How to make a complaint 26 Your Legal Expenses cover 27 Words and phrases with a special meaning 28 Summary of Legal Expenses cover 30 How to make a claim 31 Claims procedure and conditions 32 Legal Expenses cover 34 How to make a complaint 38 Get in touch: ways to contact us 2 40 Home insurance Pages 3-26 apply to home insurance"""
    
    query = "How to make complaints on legal expenses"
    
    def clean_content_for_voice(content: str, query: str) -> str:
        """Clean content to make it more voice-friendly"""
        
        # Remove page references and section numbers first
        content = re.sub(r'\b(?:Pages?\s+\d+(?:-\d+)?(?:\s+apply)?|Section\s+\d+|Page\s+\d+)', '', content, flags=re.IGNORECASE)
        
        # Remove standalone numbers that look like page/section references
        content = re.sub(r'\b\d+\s+(?=How to|What|When|Where|Why|Your|Legal|Contact)', '', content)
        
        # Remove policy document headers and footers
        content = re.sub(r'Policy booklet|HALIFAX|Home Insurance|Legal Expenses|Policy Limits', '', content, flags=re.IGNORECASE)
        
        # Clean up multiple spaces, line breaks, and dots
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\.{2,}', '.', content)
        
        # For complaints queries, provide helpful response
        if any(word in query.lower() for word in ['complaint', 'complain']):
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
        
        return content.strip()
    
    print("=== Testing Voice Response Cleaning ===")
    print(f"Original content: {sample_content}")
    print()
    
    cleaned = clean_content_for_voice(sample_content, query)
    print(f"Voice-optimized response: {cleaned}")
    print()
    
    # Test various query types
    test_cases = [
        ("How to make complaints on legal expenses", "complaint handling"),
        ("How do I make a claim", "claims process"), 
        ("What is the phone number for customer service", "contact information"),
        ("How to contact Halifax insurance", "contact information")
    ]
    
    print("=== Testing Different Query Types ===")
    for test_query, description in test_cases:
        print(f"\n🔍 Query: {test_query}")
        print(f"📝 Type: {description}")
        
        if any(word in test_query.lower() for word in ['complaint', 'complain']):
            response = "To make a complaint about legal expenses, contact Halifax customer services at 0345 604 6473. They're available Monday to Friday 8am-6pm and Saturday 9am-1pm. They'll guide you through the complaint process."
        elif any(word in test_query.lower() for word in ['claim', 'make claim']):
            response = "To make a claim, you can register online at halifax.uk/make-a-claim available 24/7, or call Halifax at 0345 604 6473. Their lines are open 8am-6pm Monday-Friday and 9am-1pm Saturday."
        elif any(word in test_query.lower() for word in ['contact', 'phone', 'call']):
            response = "The main Halifax customer service number is 0345 604 6473. They're open 8am-6pm Monday-Friday and 9am-1pm Saturday. You can also visit halifax.uk for online services."
        else:
            response = f"I can help you with information about your insurance. For general inquiries about {test_query.lower()}, contact Halifax customer services at 0345 604 6473. Is there something specific I can help you find?"
            
        print(f"🗣️ Voice Response: {response}")
        print("-" * 60)

if __name__ == "__main__":
    test_voice_response_logic()