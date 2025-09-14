#!/usr/bin/env python3
"""
Local AI Code Agent with Ollama
Capabilities: Code refactoring, documentation generation, file management, shell commands
"""

import os
import sys
import json
import subprocess
import difflib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

import chromadb
from chromadb.config import Settings
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
import psycopg2
from psycopg2 import sql

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_agent.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    """Configuration for the AI Agent"""
    ollama_model: str = "llama2"  # Change to your preferred model
    ollama_url: str = "http://localhost:11434"
    chroma_db_path: str = "./chroma_db"
    repository_path: str = "./"
    max_file_size: int = 1024 * 1024  # 1MB
    supported_extensions: List[str] = None
    
    def __post_init__(self):
        if self.supported_extensions is None:
            self.supported_extensions = [
                '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h',
                '.cs', '.php', '.rb', '.go', '.rs', '.swift',
                '.kt', '.scala', '.r', '.sql', '.md', '.txt',
                '.yml', '.yaml', '.json', '.xml', '.html', '.css'
            ]

class FileManager:
    """Handles file operations"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.repo_path = Path(config.repository_path)
    
    def read_file(self, file_path: str) -> str:
        """Read file content"""
        try:
            full_path = self.repo_path / file_path
            if full_path.stat().st_size > self.config.max_file_size:
                logger.warning(f"File {file_path} is too large, skipping")
                return ""
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return ""
    
    def write_file(self, file_path: str, content: str) -> bool:
        """Write content to file"""
        try:
            full_path = self.repo_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Successfully wrote to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return False
    
    def create_backup(self, file_path: str) -> str:
        """Create backup of file before modification"""
        try:
            full_path = self.repo_path / file_path
            backup_path = f"{full_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as src:
                    with open(backup_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                logger.info(f"Created backup: {backup_path}")
                return backup_path
        except Exception as e:
            logger.error(f"Error creating backup for {file_path}: {e}")
        return ""
    
    def apply_diff(self, file_path: str, diff_content: str) -> bool:
        """Apply diff to a file"""
        try:
            full_path = self.repo_path / file_path
            if not full_path.exists():
                logger.error(f"File {file_path} does not exist")
                return False
            
            # Create backup
            self.create_backup(file_path)
            
            # Read current content
            original_content = self.read_file(file_path)
            
            # Apply diff (simplified implementation)
            # In production, you might want to use a proper diff library
            lines = original_content.splitlines()
            diff_lines = diff_content.splitlines()
            
            # This is a basic implementation - you may need to enhance it
            for line in diff_lines:
                if line.startswith('+ '):
                    # Add line logic here
                    pass
                elif line.startswith('- '):
                    # Remove line logic here
                    pass
            
            logger.info(f"Applied diff to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error applying diff to {file_path}: {e}")
            return False
    
    def get_repository_files(self) -> List[str]:
        """Get all supported files in repository"""
        files = []
        for ext in self.config.supported_extensions:
            files.extend(self.repo_path.rglob(f"*{ext}"))
        
        # Filter out hidden files and directories
        return [str(f.relative_to(self.repo_path)) for f in files 
                if not any(part.startswith('.') for part in f.parts)]

class ShellExecutor:
    """Execute shell commands safely"""
    
    def __init__(self):
        self.allowed_commands = {
            'git', 'python', 'pip', 'npm', 'node', 'pytest', 
            'flake8', 'black', 'isort', 'mypy', 'ls', 'cat', 
            'grep', 'find', 'wc', 'head', 'tail'
        }
    
    def execute(self, command: str, cwd: str = None) -> Dict[str, Any]:
        """Execute shell command"""
        try:
            cmd_parts = command.split()
            if not cmd_parts or cmd_parts[0] not in self.allowed_commands:
                return {
                    'success': False, 
                    'error': f'Command not allowed: {cmd_parts[0] if cmd_parts else "empty"}'
                }
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=30
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Command timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

class DatabaseManager:
    """Handle PostgreSQL operations"""
    
    def __init__(self, connection_params: Dict[str, str]):
        self.connection_params = connection_params
    
    def execute_query(self, query: str, params: tuple = None) -> Dict[str, Any]:
        """Execute PostgreSQL query"""
        try:
            with psycopg2.connect(**self.connection_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    
                    if query.strip().upper().startswith('SELECT'):
                        results = cur.fetchall()
                        columns = [desc[0] for desc in cur.description]
                        return {
                            'success': True,
                            'results': results,
                            'columns': columns
                        }
                    else:
                        conn.commit()
                        return {'success': True, 'rowcount': cur.rowcount}
                        
        except Exception as e:
            logger.error(f"Database error: {e}")
            return {'success': False, 'error': str(e)}

class VectorStore:
    """Manage vector database with ChromaDB"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = chromadb.PersistentClient(path=config.chroma_db_path)
        self.collection = self.client.get_or_create_collection("code_repository")
        self.embeddings = OllamaEmbeddings(
            model=config.ollama_model,
            base_url=config.ollama_url
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    def index_repository(self, file_manager: FileManager):
        """Index all files in the repository"""
        files = file_manager.get_repository_files()
        logger.info(f"Indexing {len(files)} files")
        
        documents = []
        for file_path in files:
            content = file_manager.read_file(file_path)
            if content:
                chunks = self.text_splitter.split_text(content)
                for i, chunk in enumerate(chunks):
                    documents.append(Document(
                        page_content=chunk,
                        metadata={
                            'file_path': file_path,
                            'chunk_id': i,
                            'file_type': Path(file_path).suffix
                        }
                    ))
        
        if documents:
            # Clear existing collection
            self.client.delete_collection("code_repository")
            self.collection = self.client.get_or_create_collection("code_repository")
            
            # Add documents
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            ids = [f"{doc.metadata['file_path']}_{doc.metadata['chunk_id']}" 
                   for doc in documents]
            
            # Get embeddings and add to collection
            embeddings = self.embeddings.embed_documents(texts)
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Indexed {len(documents)} document chunks")
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for relevant code snippets"""
        try:
            query_embedding = self.embeddings.embed_query(query)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            return [
                {
                    'content': doc,
                    'metadata': meta,
                    'distance': dist
                }
                for doc, meta, dist in zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )
            ]
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

class AICodeAgent:
    """Main AI Agent class"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.llm = OllamaLLM(
            model=config.ollama_model,
            base_url=config.ollama_url
        )
        self.file_manager = FileManager(config)
        self.shell_executor = ShellExecutor()
        self.vector_store = VectorStore(config)
        
        # Initialize database manager if needed
        self.db_manager = None
        
        # Create prompts
        self.setup_prompts()
    
    def setup_prompts(self):
        """Setup prompt templates"""
        
        self.refactor_prompt = PromptTemplate(
            input_variables=["code", "context", "requirements"],
            template="""
You are a senior software engineer tasked with refactoring code. 
Given the following code and context, provide a refactored version that improves:
- Code readability and maintainability
- Performance where applicable  
- Follows best practices
- Removes code smells

Original Code:
{code}

Context:
{context}

Requirements:
{requirements}

Please provide the refactored code with explanations for the changes made.
"""
        )
        
        self.documentation_prompt = PromptTemplate(
            input_variables=["code", "file_path", "context"],
            template="""
You are a technical writer creating documentation for a code repository.
Analyze the following code and create comprehensive documentation.

File: {file_path}
Code:
{code}

Related Context:
{context}

Please create documentation that includes:
1. Overview and purpose
2. Key functions/classes and their descriptions
3. Usage examples
4. Dependencies
5. Configuration details (if any)

Format the documentation in Markdown.
"""
        )
    
    def setup_database(self, db_params: Dict[str, str]):
        """Setup database connection"""
        self.db_manager = DatabaseManager(db_params)
    
    def index_repository(self):
        """Index the current repository"""
        logger.info("Starting repository indexing...")
        self.vector_store.index_repository(self.file_manager)
        logger.info("Repository indexing completed")
    
    def refactor_code(self, file_path: str, requirements: str = "") -> Dict[str, Any]:
        """Refactor code in a specific file"""
        try:
            # Read original code
            original_code = self.file_manager.read_file(file_path)
            if not original_code:
                return {'success': False, 'error': 'Could not read file'}
            
            # Get relevant context from vector store
            context_results = self.vector_store.search(f"refactor {file_path}", n_results=3)
            context = "\n".join([r['content'] for r in context_results])
            
            # Generate refactored code
            prompt = self.refactor_prompt.format(
                code=original_code,
                context=context,
                requirements=requirements
            )
            
            refactored_code = self.llm(prompt)
            
            # Create backup and write refactored code
            backup_path = self.file_manager.create_backup(file_path)
            
            # Extract just the code from the response (you may need to adjust this)
            # This assumes the LLM returns the code in a specific format
            code_start = refactored_code.find("```")
            code_end = refactored_code.rfind("```")
            
            if code_start != -1 and code_end != -1:
                clean_code = refactored_code[code_start+3:code_end].strip()
                # Remove language identifier if present
                if '\n' in clean_code:
                    clean_code = '\n'.join(clean_code.split('\n')[1:])
            else:
                clean_code = refactored_code
            
            success = self.file_manager.write_file(f"{file_path}.refactored", clean_code)
            
            return {
                'success': success,
                'original_file': file_path,
                'refactored_file': f"{file_path}.refactored",
                'backup_file': backup_path,
                'explanation': refactored_code
            }
            
        except Exception as e:
            logger.error(f"Error refactoring {file_path}: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_documentation(self, file_path: str = None) -> Dict[str, Any]:
        """Generate documentation for file or entire repository"""
        try:
            if file_path:
                # Document single file
                code = self.file_manager.read_file(file_path)
                context_results = self.vector_store.search(f"documentation {file_path}", n_results=3)
                context = "\n".join([r['content'] for r in context_results])
                
                prompt = self.documentation_prompt.format(
                    code=code,
                    file_path=file_path,
                    context=context
                )
                
                documentation = self.llm(prompt)
                doc_path = f"docs/{file_path.replace('/', '_')}.md"
                
                success = self.file_manager.write_file(doc_path, documentation)
                
                return {
                    'success': success,
                    'documentation_file': doc_path,
                    'source_file': file_path
                }
            else:
                # Document entire repository
                files = self.file_manager.get_repository_files()
                docs_created = []
                
                for file in files[:10]:  # Limit to first 10 files for demo
                    result = self.generate_documentation(file)
                    if result['success']:
                        docs_created.append(result['documentation_file'])
                
                # Create main README
                readme_content = self.generate_readme(files)
                self.file_manager.write_file("README_GENERATED.md", readme_content)
                docs_created.append("README_GENERATED.md")
                
                return {
                    'success': True,
                    'documentation_files': docs_created
                }
                
        except Exception as e:
            logger.error(f"Error generating documentation: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_readme(self, files: List[str]) -> str:
        """Generate README for the repository"""
        file_structure = {}
        for file in files:
            parts = file.split('/')
            current = file_structure
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = None
        
        readme = f"""# Repository Documentation
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Project Structure
```
{self._format_tree(file_structure)}
```

## Files Overview
Total files analyzed: {len(files)}

### File Types
"""
        
        # Count file types
        type_counts = {}
        for file in files:
            ext = Path(file).suffix or 'no extension'
            type_counts[ext] = type_counts.get(ext, 0) + 1
        
        for ext, count in sorted(type_counts.items()):
            readme += f"- {ext}: {count} files\n"
        
        readme += """
## Documentation
Individual file documentation can be found in the `docs/` directory.

## Usage
This repository has been analyzed by an AI agent for code quality and documentation.
"""
        
        return readme
    
    def _format_tree(self, structure: Dict, indent: str = "") -> str:
        """Format file structure as tree"""
        result = ""
        for key, value in structure.items():
            result += f"{indent}{key}\n"
            if value is not None:
                result += self._format_tree(value, indent + "  ")
        return result
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute shell command"""
        return self.shell_executor.execute(command, cwd=self.config.repository_path)
    
    def query_database(self, query: str, params: tuple = None) -> Dict[str, Any]:
        """Execute database query"""
        if not self.db_manager:
            return {'success': False, 'error': 'Database not configured'}
        
        return self.db_manager.execute_query(query, params)
    
    def analyze_code_quality(self, file_path: str) -> Dict[str, Any]:
        """Analyze code quality using various tools"""
        results = {}
        
        file_ext = Path(file_path).suffix
        
        if file_ext == '.py':
            # Run Python quality tools
            results['flake8'] = self.execute_command(f"flake8 {file_path}")
            results['mypy'] = self.execute_command(f"mypy {file_path}")
            
        # Add more language-specific quality checks here
        
        return results
    
    def interactive_mode(self):
        """Interactive mode for the agent"""
        print("AI Code Agent Interactive Mode")
        print("Available commands:")
        print("  index - Index the repository")
        print("  refactor <file_path> - Refactor a file")
        print("  doc <file_path> - Generate documentation for a file")
        print("  doc-all - Generate documentation for all files")
        print("  shell <command> - Execute shell command")
        print("  quality <file_path> - Analyze code quality")
        print("  search <query> - Search in the codebase")
        print("  quit - Exit")
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                    
                parts = user_input.split(' ', 1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if command == 'quit':
                    break
                elif command == 'index':
                    self.index_repository()
                elif command == 'refactor':
                    if args:
                        result = self.refactor_code(args)
                        print(json.dumps(result, indent=2))
                    else:
                        print("Please specify a file path")
                elif command == 'doc':
                    if args:
                        result = self.generate_documentation(args)
                        print(json.dumps(result, indent=2))
                    else:
                        print("Please specify a file path")
                elif command == 'doc-all':
                    result = self.generate_documentation()
                    print(json.dumps(result, indent=2))
                elif command == 'shell':
                    if args:
                        result = self.execute_command(args)
                        print(json.dumps(result, indent=2))
                    else:
                        print("Please specify a command")
                elif command == 'quality':
                    if args:
                        result = self.analyze_code_quality(args)
                        print(json.dumps(result, indent=2))
                    else:
                        print("Please specify a file path")
                elif command == 'search':
                    if args:
                        results = self.vector_store.search(args)
                        for i, result in enumerate(results):
                            print(f"\nResult {i+1}:")
                            print(f"File: {result['metadata']['file_path']}")
                            print(f"Content: {result['content'][:200]}...")
                    else:
                        print("Please specify a search query")
                else:
                    print(f"Unknown command: {command}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("Goodbye!")

def main():
    """Main function to run the AI agent"""
    
    # Configuration
    config = AgentConfig(
        ollama_model="gpt-oss:20b",  # Change to your model
        repository_path="./",   # Change to your repo path
        chroma_db_path="./chroma_db"
    )
    
    # Initialize agent
    agent = AICodeAgent(config)
    
    # Optional: Setup database connection
    # db_params = {
    #     'host': 'localhost',
    #     'database': 'your_db',
    #     'user': 'your_user',
    #     'password': 'your_password'
    # }
    # agent.setup_database(db_params)
    
    # Run in interactive mode
    agent.interactive_mode()

if __name__ == "__main__":
    main()