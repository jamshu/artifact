#!/usr/bin/env python3

import sys
import os
from ai_agent import AgentConfig, AICodeAgent

def test_documentation():
    """Test documentation generation functionality"""
    
    # Configuration  
    config = AgentConfig(
        ollama_model="llama3.2",
        repository_path="./",
        chroma_db_path="./chroma_db"
    )
    
    # Initialize agent
    agent = AICodeAgent(config)
    
    # Test documentation generation for the test file
    print("Testing documentation generation...")
    result = agent.generate_documentation("test_file.js")
    
    print(f"Result: {result}")
    
    if result['success']:
        print(f"\nDocumentation generated successfully!")
        print(f"Documentation file: {result['documentation_file']}")
        print(f"Source file: {result['source_file']}")
        
        # Read and display the generated documentation
        if os.path.exists(result['documentation_file']):
            print(f"\nGenerated documentation content:")
            print("=" * 50)
            with open(result['documentation_file'], 'r') as f:
                print(f.read())
            print("=" * 50)
        else:
            print(f"Warning: Documentation file {result['documentation_file']} was not created")
    else:
        print(f"Documentation generation failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_documentation()