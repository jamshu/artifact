#!/usr/bin/env python3
"""
LangChain-based Gemini-Powered Odoo Agent
Refactored to use LangChain for better LLM abstraction and prompt management
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.prompt import Confirm, Prompt
from rich import print as rprint

from langchain_core.language_models import BaseLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

from llm_config import LLMConfig
from prompts import get_prompt_template

load_dotenv()

console = Console()


@dataclass
class FileChange:
    """Represents a file change operation"""
    file_path: str
    action: str  # 'create', 'modify', 'delete'
    original_content: str
    new_content: str
    description: str


class LangChainOdooAgent:
    """LangChain-based Odoo development agent"""
    
    def __init__(self, provider: str = None):
        """Initialize the agent with specified LLM provider"""
        self.load_config()
        
        # Initialize LLM configuration
        self.llm_config = LLMConfig(provider)
        self.llm = self.llm_config.get_llm()
        
        # Output parsers
        self.json_parser = JsonOutputParser()
        self.str_parser = StrOutputParser()
        
        console.print(f"✅ LangChain Odoo Agent initialized with {self.llm_config.get_provider_info()}")
        
    def load_config(self):
        """Load configuration from environment variables"""
        self.odoo_addons_path = Path(os.getenv("ODOO_ADDONS_PATH", "/opt/odoo/addons"))
        self.odoo_version = os.getenv("ODOO_VERSION", "16.0")
        self.agent_mode = os.getenv("AGENT_MODE", "development")
        self.auto_approve = os.getenv("AUTO_APPROVE_CHANGES", "false").lower() == "true"
        self.backup_files = os.getenv("BACKUP_FILES", "true").lower() == "true"
        
        if not self.odoo_addons_path.exists():
            console.print(f"[yellow]Warning: Odoo addons path doesn't exist: {self.odoo_addons_path}[/yellow]")
    
    def analyze_existing_code(self, file_path: str) -> Dict:
        """Analyze existing Odoo code using LangChain"""
        try:
            full_path = self.odoo_addons_path / file_path
            if not full_path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}
            
            with open(full_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
            
            # Get prompt template and format it
            prompt_template = get_prompt_template("code_analysis")
            prompt = prompt_template.format(
                odoo_version=self.odoo_version,
                file_path=file_path,
                code_content=code_content
            )
            
            # Create chain and invoke
            chain = prompt_template | self.llm | self.str_parser
            response = chain.invoke({
                "odoo_version": self.odoo_version,
                "file_path": file_path,
                "code_content": code_content
            })
            
            return {
                "success": True,
                "file_path": file_path,
                "analysis": response,
                "code_quality": "analysis_complete"
            }
            
        except Exception as e:
            console.print(f"[red]Error analyzing code: {e}[/red]")
            return {"success": False, "error": str(e)}
    
    def create_odoo_module(self, module_name: str, description: str, features: str) -> Dict:
        """Create a new Odoo module using LangChain"""
        try:
            # Get prompt template and create chain
            prompt_template = get_prompt_template("module_creation")
            chain = prompt_template | self.llm | self.str_parser
            
            # Invoke chain
            response = chain.invoke({
                "odoo_version": self.odoo_version,
                "module_name": module_name,
                "description": description,
                "features": features
            })
            
            # Parse JSON response safely
            module_data = self.parse_json_response(response)
            if not module_data:
                return {"success": False, "error": "Failed to parse LLM response as JSON"}
            
            # Create file changes for approval
            module_path = self.odoo_addons_path / module_name
            changes = []
            
            for file_info in module_data.get('files', []):
                file_path = module_path / file_info['path']
                
                change = FileChange(
                    file_path=str(file_path),
                    action='create',
                    original_content='',
                    new_content=file_info['content'],
                    description=f"Create {file_info['path']}: {file_info.get('description', 'No description')}"
                )
                changes.append(change)
            
            # Show changes for approval
            if self.show_changes_for_approval(changes, f"Create module: {module_name}"):
                self.apply_changes(changes)
                return {
                    "success": True,
                    "module_name": module_name,
                    "module_path": str(module_path),
                    "files_created": len(changes)
                }
            else:
                return {"success": False, "message": "Module creation cancelled by user"}
                
        except Exception as e:
            console.print(f"[red]Error creating module: {e}[/red]")
            return {"success": False, "error": str(e)}
    
    def customize_existing_module(self, module_path: str, customization_request: str) -> Dict:
        """Customize an existing Odoo module using LangChain"""
        try:
            module_path = Path(module_path)
            if not module_path.exists():
                return {"success": False, "error": f"Module not found: {module_path}"}
            
            # Read existing files
            existing_files = self.get_module_files(module_path)
            
            # Get prompt template and create chain
            prompt_template = get_prompt_template("module_customization")
            chain = prompt_template | self.llm | self.str_parser
            
            # Invoke chain
            response = chain.invoke({
                "odoo_version": self.odoo_version,
                "customization_request": customization_request,
                "existing_files": json.dumps(existing_files, indent=2)
            })
            
            # Parse JSON response
            customization_data = self.parse_json_response(response)
            if not customization_data:
                return {"success": False, "error": "Failed to parse LLM response as JSON"}
            
            # Create file changes
            changes = []
            for change_info in customization_data.get('changes', []):
                full_path = module_path / change_info['file_path']
                
                original_content = ''
                if full_path.exists():
                    with open(full_path, 'r', encoding='utf-8') as f:
                        original_content = f.read()
                
                change = FileChange(
                    file_path=str(full_path),
                    action=change_info['action'],
                    original_content=original_content,
                    new_content=change_info.get('new_content', ''),
                    description=f"{change_info['action'].title()} {change_info['file_path']}: {change_info.get('explanation', 'No explanation')}"
                )
                changes.append(change)
            
            # Show changes for approval
            if self.show_changes_for_approval(changes, f"Customize module: {module_path.name}"):
                self.apply_changes(changes)
                return {
                    "success": True,
                    "module_path": str(module_path),
                    "changes_applied": len(changes),
                    "analysis": customization_data.get('analysis', '')
                }
            else:
                return {"success": False, "message": "Customization cancelled by user"}
                
        except Exception as e:
            console.print(f"[red]Error customizing module: {e}[/red]")
            return {"success": False, "error": str(e)}
    
    def debug_odoo_issue(self, error_message: str, code_context: str, module_path: str = None) -> Dict:
        """Debug Odoo issues using LangChain"""
        try:
            context_info = "No specific module context provided."
            if module_path:
                module_path = Path(module_path)
                if module_path.exists():
                    relevant_files = self.get_module_files(module_path, file_types=[".py"])
                    context_info = f"Module files:\n{json.dumps(relevant_files, indent=2)}"
            
            # Get prompt template and create chain
            prompt_template = get_prompt_template("debug_issue")
            chain = prompt_template | self.llm | self.str_parser
            
            # Invoke chain
            response = chain.invoke({
                "odoo_version": self.odoo_version,
                "error_message": error_message,
                "code_context": code_context,
                "context_info": context_info
            })
            
            # Try to parse as JSON for structured fixes
            debug_data = self.parse_json_response(response)
            
            if debug_data and 'fixes' in debug_data:
                # Create file changes if fixes are provided
                changes = []
                for fix in debug_data.get('fixes', []):
                    if module_path:
                        full_path = Path(module_path) / fix['file_path']
                    else:
                        full_path = Path(fix['file_path'])
                    
                    original_content = ''
                    if full_path.exists():
                        with open(full_path, 'r', encoding='utf-8') as f:
                            original_content = f.read()
                    
                    change = FileChange(
                        file_path=str(full_path),
                        action=fix['action'],
                        original_content=original_content,
                        new_content=fix['new_content'],
                        description=f"Debug fix: {fix.get('explanation', 'No explanation')}"
                    )
                    changes.append(change)
                
                # Show debug analysis
                console.print(Panel(Markdown(debug_data.get('diagnosis', 'No diagnosis provided')), title="🔍 Root Cause Analysis"))
                console.print(Panel(Markdown(debug_data.get('solution', 'No solution provided')), title="💡 Solution Strategy"))
                
                if changes:
                    if self.show_changes_for_approval(changes, "Apply debug fixes"):
                        self.apply_changes(changes)
                        return {
                            "success": True,
                            "fixes_applied": len(changes),
                            "diagnosis": debug_data.get('diagnosis', ''),
                            "testing_instructions": debug_data.get('testing_instructions', '')
                        }
                    else:
                        return {"success": False, "message": "Debug fixes cancelled by user"}
                else:
                    return {
                        "success": True,
                        "diagnosis": debug_data.get('diagnosis', ''),
                        "solution": debug_data.get('solution', ''),
                        "message": "Analysis completed - no code changes needed"
                    }
            else:
                # Plain text analysis
                console.print(Panel(Markdown(response), title="🔍 Debug Analysis"))
                return {
                    "success": True,
                    "analysis": response,
                    "message": "Debug analysis completed"
                }
                
        except Exception as e:
            console.print(f"[red]Error debugging issue: {e}[/red]")
            return {"success": False, "error": str(e)}
    
    def parse_json_response(self, response: str) -> Optional[Dict]:
        """Safely parse JSON response from LLM"""
        try:
            # Clean up the response text
            response_text = response.strip()
            
            # Remove markdown code blocks
            if response_text.startswith('```json'):
                response_text = response_text[7:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Try to parse JSON
            return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            console.print(f"[red]Error parsing LLM response as JSON: {e}[/red]")
            console.print(f"[yellow]Raw response:[/yellow] {response_text[:500]}...")
            
            # Try to extract JSON from partial response
            try:
                start_idx = response_text.find('{')
                if start_idx == -1:
                    return None
                
                brace_count = 0
                end_idx = start_idx
                for i, char in enumerate(response_text[start_idx:], start_idx):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                
                if brace_count == 0:
                    partial_json = response_text[start_idx:end_idx]
                    return json.loads(partial_json)
                    
            except (ValueError, json.JSONDecodeError):
                pass
            
            return None
    
    def get_module_files(self, module_path: Path, file_types: List[str] = None) -> Dict[str, str]:
        """Get files from a module directory"""
        if file_types is None:
            file_types = [".py", ".xml", ".csv", ".yml", ".yaml"]
        
        files = {}
        for file_type in file_types:
            for file_path in module_path.rglob(f"*{file_type}"):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            files[str(file_path.relative_to(module_path))] = f.read()
                    except Exception as e:
                        console.print(f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]")
        
        return files
    
    def show_changes_for_approval(self, changes: List[FileChange], title: str) -> bool:
        """Show proposed changes and get user approval"""
        
        if not changes:
            console.print("[yellow]No changes to apply[/yellow]")
            return False
        
        console.print(f"\n[bold cyan]📋 {title}[/bold cyan]")
        console.print(f"[dim]Proposed changes: {len(changes)} files[/dim]\n")
        
        # Show summary table
        table = Table(title="Proposed Changes")
        table.add_column("Action", style="bold")
        table.add_column("File", style="cyan")
        table.add_column("Description", style="dim")
        
        for change in changes:
            file_name = Path(change.file_path).name
            table.add_row(
                change.action.upper(),
                file_name,
                change.description[:60] + "..." if len(change.description) > 60 else change.description
            )
        
        console.print(table)
        
        # If auto-approve is enabled, skip interactive approval
        if self.auto_approve:
            console.print("[green]✅ Auto-approve enabled - applying changes[/green]")
            return True
        
        # Ask for approval
        if not Confirm.ask("\n[bold]Do you want to review the changes in detail?[/bold]", default=True):
            return Confirm.ask("[bold]Apply changes without detailed review?[/bold]", default=False)
        
        # Show detailed diffs
        for i, change in enumerate(changes, 1):
            console.print(f"\n[bold cyan]📄 Change {i}/{len(changes)}: {Path(change.file_path).name}[/bold cyan]")
            console.print(f"[dim]Action: {change.action} | Path: {change.file_path}[/dim]")
            console.print(f"[dim]Description: {change.description}[/dim]\n")
            
            if change.action == 'create':
                console.print("[green]📝 New file content:[/green]")
                console.print(Panel(change.new_content[:1000] + "..." if len(change.new_content) > 1000 else change.new_content))
            elif change.action == 'modify':
                console.print("[yellow]📝 Modified content:[/yellow]")
                console.print(Panel(change.new_content[:1000] + "..." if len(change.new_content) > 1000 else change.new_content))
            elif change.action == 'delete':
                console.print("[red]🗑️ File will be deleted[/red]")
            
            if i < len(changes):
                if not Confirm.ask(f"\n[bold]Continue to next change ({i+1}/{len(changes)})?[/bold]", default=True):
                    break
        
        return Confirm.ask("\n[bold green]Apply all changes?[/bold green]", default=True)
    
    def apply_changes(self, changes: List[FileChange]):
        """Apply the proposed file changes"""
        success_count = 0
        
        for change in changes:
            try:
                file_path = Path(change.file_path)
                
                # Create parent directories if needed
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Backup original file if it exists and backup is enabled
                if self.backup_files and file_path.exists():
                    backup_path = file_path.with_suffix(f"{file_path.suffix}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                    file_path.rename(backup_path)
                    console.print(f"[dim]📦 Backup created: {backup_path.name}[/dim]")
                
                if change.action == 'create' or change.action == 'modify':
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(change.new_content)
                    console.print(f"[green]✅ {change.action.title()}: {file_path.name}[/green]")
                elif change.action == 'delete':
                    if file_path.exists():
                        file_path.unlink()
                        console.print(f"[red]🗑️ Deleted: {file_path.name}[/red]")
                
                success_count += 1
                
            except Exception as e:
                console.print(f"[red]❌ Failed to apply change to {change.file_path}: {e}[/red]")
        
        console.print(f"\n[bold green]✅ Applied {success_count}/{len(changes)} changes successfully[/bold green]")
    
    def get_provider_info(self) -> Dict:
        """Get current LLM provider information"""
        return self.llm_config.get_provider_info()


def main():
    """CLI interface for the LangChain Odoo agent"""
    console.print("[bold blue]🤖 LangChain-Powered Odoo Development Agent[/bold blue]")
    
    # Initialize agent
    try:
        agent = LangChainOdooAgent()
    except Exception as e:
        console.print(f"[red]Failed to initialize agent: {e}[/red]")
        sys.exit(1)
    
    # Show provider info
    provider_info = agent.get_provider_info()
    console.print(f"[dim]Using {provider_info['provider']} ({provider_info['model']})[/dim]")
    
    while True:
        console.print("\n[bold cyan]Available Actions:[/bold cyan]")
        console.print("1. 🔍 Analyze existing code")
        console.print("2. 🔧 Create new module")
        console.print("3. ⚙️ Customize existing module")
        console.print("4. 🐛 Debug Odoo issue")
        console.print("5. ❌ Exit")
        
        choice = Prompt.ask("Choose an action", choices=["1", "2", "3", "4", "5"])
        
        if choice == "1":
            file_path = Prompt.ask("Enter file path to analyze")
            result = agent.analyze_existing_code(file_path)
            if result["success"]:
                console.print(Panel(Markdown(result["analysis"]), title="Code Analysis"))
            else:
                console.print(f"[red]Error: {result['error']}[/red]")
                
        elif choice == "2":
            module_name = Prompt.ask("Enter module name")
            description = Prompt.ask("Enter module description")
            features = Prompt.ask("Enter features description")
            result = agent.create_odoo_module(module_name, description, features)
            console.print(result)
            
        elif choice == "3":
            module_path = Prompt.ask("Enter module path")
            request = Prompt.ask("Enter customization request")
            result = agent.customize_existing_module(module_path, request)
            console.print(result)
            
        elif choice == "4":
            error_message = Prompt.ask("Enter error message")
            code_context = Prompt.ask("Enter code context")
            module_path = Prompt.ask("Enter module path (optional)", default="")
            result = agent.debug_odoo_issue(error_message, code_context, module_path or None)
            console.print(result)
            
        elif choice == "5":
            console.print("[green]👋 Goodbye![/green]")
            break


if __name__ == "__main__":
    main()