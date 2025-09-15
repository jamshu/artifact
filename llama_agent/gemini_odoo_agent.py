#!/usr/bin/env python3
"""
Gemini-Powered Odoo 16 Development Agent
Advanced AI assistant for Odoo development with interactive diff approval
"""

import os
import sys
import json
import difflib
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

import google.generativeai as genai
from dotenv import load_dotenv
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.markdown import Markdown

# Load environment variables
load_dotenv()

console = Console()

@dataclass
class FileChange:
    """Represents a proposed file change"""
    file_path: str
    action: str  # 'create', 'modify', 'delete'
    original_content: str
    new_content: str
    description: str

class GeminiOdooAgent:
    """Gemini-powered Odoo development agent with interactive approval"""
    
    def __init__(self, config_path: str = ".env"):
        """Initialize the Gemini Odoo agent"""
        self.load_config()
        self.setup_gemini()
        self.pending_changes: List[FileChange] = []
        
    def load_config(self):
        """Load configuration from environment variables"""
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.odoo_addons_path = Path(os.getenv("ODOO_ADDONS_PATH", "./test_modules"))
        self.odoo_version = os.getenv("ODOO_VERSION", "16.0")
        self.agent_mode = os.getenv("AGENT_MODE", "development")
        self.auto_approve = os.getenv("AUTO_APPROVE_CHANGES", "false").lower() == "true"
        self.backup_files = os.getenv("BACKUP_FILES", "true").lower() == "true"
        
        if not self.gemini_api_key or self.gemini_api_key == "your_api_key_here":
            console.print("[red]❌ Error: GEMINI_API_KEY not found in .env file[/red]")
            console.print("[yellow]Please add your Gemini API key to the .env file[/yellow]")
            sys.exit(1)
    
    def setup_gemini(self):
        """Configure Gemini API"""
        genai.configure(api_key=self.gemini_api_key)
        
        # Configure safety settings for code generation
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH", 
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
        
        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name='gemini-2.0-flash-exp',
            safety_settings=safety_settings,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                top_k=40,
                max_output_tokens=16384  # Increased for larger responses
            )
        )
        
        console.print("✅ Gemini 2.0 Flash configured successfully")
    
    def parse_gemini_json_response(self, response_text: str) -> dict:
        """Safely parse JSON response from Gemini"""
        try:
            # Clean up the response text
            response_text = response_text.strip()
            
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
            console.print(f"[red]Error parsing Gemini response: {e}[/red]")
            console.print("[yellow]Raw response:[/yellow]")
            console.print(response_text[:2000] + "..." if len(response_text) > 2000 else response_text)
            
            # Try to extract JSON from partial response
            try:
                # Find the start of JSON
                start_idx = response_text.find('{')
                if start_idx == -1:
                    raise ValueError("No JSON found in response")
                
                # Try to find a complete JSON object by counting braces
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
                else:
                    raise ValueError("Incomplete JSON response")
                    
            except (ValueError, json.JSONDecodeError) as parse_error:
                console.print(f"[red]Failed to parse partial JSON: {parse_error}[/red]")
                raise e
    
    def analyze_existing_code(self, file_path: str) -> Dict:
        """Analyze existing Odoo code and suggest improvements"""
        try:
            full_path = self.odoo_addons_path / file_path
            if not full_path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}
            
            with open(full_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
            
            prompt = f"""
            You are an expert Odoo {self.odoo_version} developer. Analyze the following code and provide detailed feedback:

            File: {file_path}
            Code:
            ```python
            {code_content}
            ```

            Please provide:

            1. **Code Quality Assessment** - Rate the code quality (1-10) and explain
            2. **Odoo Best Practices** - Check compliance with Odoo coding standards
            3. **Performance Issues** - Identify potential performance problems
            4. **Security Concerns** - Highlight any security vulnerabilities
            5. **Refactoring Suggestions** - Specific improvements with code examples
            6. **Missing Features** - Suggest additional Odoo features that could be implemented

            Focus on Odoo-specific patterns like:
            - Proper model inheritance
            - Field definitions and relationships
            - API decorators usage
            - Security rules
            - View inheritance
            - Computed fields and dependencies

            Provide actionable suggestions with code examples.
            """
            
            response = self.model.generate_content(prompt)
            
            return {
                "success": True,
                "file_path": file_path,
                "analysis": response.text,
                "code_quality": "analysis_complete"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_odoo_module(self, module_name: str, description: str, features: str) -> Dict:
        """Create a new Odoo module with interactive approval"""
        
        prompt = f"""
        You are an expert Odoo {self.odoo_version} developer. Create a complete, production-ready Odoo module:

        **Module Details:**
        - Name: {module_name}
        - Description: {description}
        - Features: {features}
        - Odoo Version: {self.odoo_version}

        **Requirements:**
        1. Create a complete module structure with all necessary files
        2. Follow Odoo {self.odoo_version} best practices and coding standards
        3. Include proper security rules and access rights
        4. Add comprehensive views (form, tree, search, actions, menus)
        5. Include sample data if appropriate
        6. Add proper field validations and constraints
        7. Use modern Odoo patterns and decorators

        **Generate the following files with complete, working code:**

        1. **__manifest__.py** - Complete manifest with dependencies and data files
        2. **__init__.py** - Module initialization
        3. **models/__init__.py** and **models/[model_files].py** - All model definitions
        4. **views/[view_files].xml** - All views, actions, and menus
        5. **security/ir.model.access.csv** - Complete access rights
        6. **data/[data_files].xml** - Sample/default data if needed
        7. **static/description/index.html** - Module description

        For each file, provide:
        - Full file path relative to module root
        - Complete file contents
        - Brief explanation of the file's purpose

        **IMPORTANT: Return ONLY a valid JSON response with this exact structure:**
        
        ```json
        {{
            "module_info": {{
                "name": "{module_name}",
                "description": "{description}",
                "features": "{features}"
            }},
            "files": [
                {{
                    "path": "relative/file/path",
                    "content": "complete file content",
                    "description": "file purpose"
                }}
            ]
        }}
        ```

        - Use double quotes for all JSON strings
        - Escape special characters properly (\n, \", \\)
        - Keep file content concise but complete
        - Ensure the JSON is valid and properly closed
        - Do not include any text outside the JSON structure
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Parse the JSON response using safe parser
            module_data = self.parse_gemini_json_response(response.text)
            
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
                    description=f"Create {file_info['path']}: {file_info['description']}"
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
            return {"success": False, "error": str(e)}
    
    def customize_existing_module(self, module_path: str, customization_request: str) -> Dict:
        """Customize an existing Odoo module"""
        
        module_path = Path(module_path)
        if not module_path.exists():
            return {"success": False, "error": f"Module not found: {module_path}"}
        
        # Read existing files
        existing_files = {}
        for file_path in module_path.rglob("*.py"):
            if file_path.is_file():
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_files[str(file_path.relative_to(module_path))] = f.read()
        
        for file_path in module_path.rglob("*.xml"):
            if file_path.is_file():
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_files[str(file_path.relative_to(module_path))] = f.read()
        
        # Create customization prompt
        prompt = f"""
        You are an expert Odoo {self.odoo_version} developer. Analyze the existing module and implement the requested customization:

        **Customization Request:** {customization_request}

        **Existing Module Files:**
        {json.dumps(existing_files, indent=2)}

        **Requirements:**
        1. Analyze the existing code structure
        2. Implement the requested customization following Odoo best practices
        3. Preserve existing functionality
        4. Add proper inheritance where needed
        5. Update or create necessary views
        6. Add security rules if needed
        7. Update the manifest if new dependencies are required

        **Provide response as JSON:**
        {{
            "analysis": "Brief analysis of existing code and customization approach",
            "changes": [
                {{
                    "action": "modify|create|delete",
                    "file_path": "relative/path/to/file",
                    "new_content": "complete new file content",
                    "explanation": "why this change is needed"
                }}
            ]
        }}

        Only include files that need to be modified or created. For modifications, provide the complete new file content.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Parse response using safe parser
            customization_data = self.parse_gemini_json_response(response.text)
            
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
                    new_content=change_info['new_content'],
                    description=f"{change_info['action'].title()} {change_info['file_path']}: {change_info['explanation']}"
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
            return {"success": False, "error": str(e)}
    
    def debug_odoo_issue(self, error_message: str, code_context: str, module_path: str = None) -> Dict:
        """Debug Odoo issues and suggest fixes"""
        
        context_info = "No specific module context provided."
        if module_path:
            module_path = Path(module_path)
            if module_path.exists():
                # Gather relevant files
                relevant_files = {}
                for file_path in module_path.rglob("*.py"):
                    if file_path.is_file():
                        with open(file_path, 'r', encoding='utf-8') as f:
                            relevant_files[str(file_path.relative_to(module_path))] = f.read()
                
                context_info = f"Module files:\n{json.dumps(relevant_files, indent=2)}"
        
        prompt = f"""
        You are an expert Odoo {self.odoo_version} debugger. Analyze and fix the following issue:

        **Error Message:** {error_message}
        **Code Context:** {code_context}
        **Module Context:** {context_info}

        **Provide comprehensive debugging assistance:**

        1. **Root Cause Analysis** - Identify the exact cause of the error
        2. **Solution Strategy** - Explain the approach to fix the issue
        3. **Code Fixes** - Provide specific code changes needed
        4. **Prevention** - How to avoid similar issues in the future
        5. **Testing** - How to verify the fix works
        6. **Related Issues** - Other potential problems that might arise

        **Focus on Odoo-specific debugging:**
        - Model inheritance issues
        - Field definition problems
        - View inheritance conflicts
        - Security access issues
        - Module dependency problems
        - ORM usage errors
        - API decorator issues

        If code changes are needed, provide them in this JSON format:
        {{
            "diagnosis": "Detailed explanation of the problem",
            "solution": "High-level solution approach", 
            "fixes": [
                {{
                    "file_path": "path/to/file",
                    "action": "modify|create",
                    "new_content": "complete fixed content",
                    "explanation": "why this fix is needed"
                }}
            ],
            "testing_instructions": "How to test the fix",
            "prevention_tips": "How to avoid this in the future"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Try to parse as JSON for code fixes
            response_text = response.text.strip()
            
            try:
                if response_text.startswith('```json'):
                    response_text = response_text[7:-3]
                elif response_text.startswith('```'):
                    response_text = response_text[3:-3]
                    
                debug_data = json.loads(response_text)
                
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
                        description=f"Debug fix: {fix['explanation']}"
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
                    
            except json.JSONDecodeError:
                # If not JSON, treat as plain text analysis
                console.print(Panel(Markdown(response.text), title="🔍 Debug Analysis"))
                return {
                    "success": True,
                    "analysis": response.text,
                    "message": "Debug analysis completed"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
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
                syntax = Syntax(change.new_content, "python", theme="monokai", line_numbers=True)
                console.print(syntax)
            
            elif change.action == 'modify':
                console.print("[yellow]🔄 File diff:[/yellow]")
                diff = self.generate_diff(change.original_content, change.new_content, change.file_path)
                if diff:
                    console.print(diff)
                else:
                    console.print("[dim]No differences found[/dim]")
            
            elif change.action == 'delete':
                console.print("[red]🗑️  File will be deleted[/red]")
            
            # Ask for individual approval
            choice = Prompt.ask(
                f"\n[bold]Action for {Path(change.file_path).name}[/bold]",
                choices=["approve", "skip", "edit", "cancel"],
                default="approve"
            )
            
            if choice == "cancel":
                return False
            elif choice == "skip":
                changes.remove(change)
            elif choice == "edit":
                # Allow manual editing
                new_content = self.edit_content_interactively(change.new_content)
                if new_content is not None:
                    change.new_content = new_content
                else:
                    changes.remove(change)
        
        if not changes:
            console.print("[yellow]No changes remaining to apply[/yellow]")
            return False
        
        # Final confirmation
        return Confirm.ask(f"\n[bold green]Apply {len(changes)} changes?[/bold green]", default=True)
    
    def generate_diff(self, original: str, new: str, file_path: str) -> str:
        """Generate a colored diff between original and new content"""
        
        original_lines = original.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            new_lines,
            fromfile=f"a/{Path(file_path).name}",
            tofile=f"b/{Path(file_path).name}",
            lineterm=""
        )
        
        diff_text = ''.join(diff)
        if not diff_text:
            return None
            
        # Apply color coding
        colored_diff = []
        for line in diff_text.splitlines():
            if line.startswith('+++'):
                colored_diff.append(f"[bold green]{line}[/bold green]")
            elif line.startswith('---'):
                colored_diff.append(f"[bold red]{line}[/bold red]")
            elif line.startswith('@@'):
                colored_diff.append(f"[cyan]{line}[/cyan]")
            elif line.startswith('+'):
                colored_diff.append(f"[green]{line}[/green]")
            elif line.startswith('-'):
                colored_diff.append(f"[red]{line}[/red]")
            else:
                colored_diff.append(line)
        
        return '\n'.join(colored_diff)
    
    def edit_content_interactively(self, content: str) -> Optional[str]:
        """Allow interactive editing of content"""
        
        temp_file = Path(f"/tmp/gemini_edit_{datetime.now().timestamp()}.py")
        
        try:
            # Write content to temp file
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Open in default editor
            editor = os.getenv('EDITOR', 'nano')
            os.system(f"{editor} {temp_file}")
            
            # Read modified content
            if temp_file.exists():
                with open(temp_file, 'r', encoding='utf-8') as f:
                    modified_content = f.read()
                
                if modified_content != content:
                    return modified_content
            
            return None
            
        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()
    
    def apply_changes(self, changes: List[FileChange]):
        """Apply the approved changes to files"""
        
        console.print("\n[bold green]🔄 Applying changes...[/bold green]")
        
        applied_changes = 0
        
        for change in changes:
            try:
                file_path = Path(change.file_path)
                
                # Create backup if file exists and backups are enabled
                if self.backup_files and file_path.exists():
                    backup_path = file_path.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_path.suffix}")
                    shutil.copy2(file_path, backup_path)
                    console.print(f"[dim]📋 Backup created: {backup_path.name}[/dim]")
                
                # Apply the change
                if change.action == 'create' or change.action == 'modify':
                    # Ensure directory exists
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Write new content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(change.new_content)
                    
                    action_icon = "📄" if change.action == 'create' else "✏️"
                    console.print(f"[green]{action_icon} {change.action.title()}: {file_path.name}[/green]")
                
                elif change.action == 'delete':
                    file_path.unlink()
                    console.print(f"[red]🗑️  Deleted: {file_path.name}[/red]")
                
                applied_changes += 1
                
            except Exception as e:
                console.print(f"[red]❌ Error applying change to {file_path.name}: {e}[/red]")
        
        console.print(f"\n[bold green]✅ Applied {applied_changes}/{len(changes)} changes successfully[/bold green]")
    
    def interactive_mode(self):
        """Run the agent in interactive mode"""
        
        console.print(Panel(
            "[bold cyan]🤖 Gemini-Powered Odoo 16 Development Agent[/bold cyan]\n"
            "[dim]Advanced AI assistant with interactive diff approval[/dim]",
            title="Welcome"
        ))
        
        console.print("\n[bold]Available Commands:[/bold]")
        commands_table = Table()
        commands_table.add_column("Command", style="cyan")
        commands_table.add_column("Description", style="dim")
        
        commands_table.add_row("analyze <file_path>", "Analyze existing code and suggest improvements")
        commands_table.add_row("create <module_name> <description> <features>", "Create a new Odoo module")
        commands_table.add_row("customize <module_path> <request>", "Customize an existing module")
        commands_table.add_row("debug <error> <context> [module_path]", "Debug Odoo issues")
        commands_table.add_row("config", "Show current configuration")
        commands_table.add_row("help", "Show this help message")
        commands_table.add_row("quit", "Exit the agent")
        
        console.print(commands_table)
        
        while True:
            try:
                user_input = Prompt.ask("\n[bold cyan]🤖 gemini-agent[/bold cyan]").strip()
                
                if not user_input:
                    continue
                
                parts = user_input.split(' ', 2)
                command = parts[0].lower()
                
                if command == 'quit':
                    console.print("[yellow]👋 Goodbye![/yellow]")
                    break
                
                elif command == 'help':
                    console.print(commands_table)
                
                elif command == 'config':
                    self.show_config()
                
                elif command == 'analyze':
                    if len(parts) < 2:
                        console.print("[red]Usage: analyze <file_path>[/red]")
                        continue
                    
                    result = self.analyze_existing_code(parts[1])
                    if result['success']:
                        console.print(Panel(Markdown(result['analysis']), title=f"📊 Analysis: {parts[1]}"))
                    else:
                        console.print(f"[red]❌ Error: {result['error']}[/red]")
                
                elif command == 'create':
                    if len(parts) < 4:
                        console.print("[red]Usage: create <module_name> <description> <features>[/red]")
                        continue
                    
                    args = user_input.split(' ', 3)
                    result = self.create_odoo_module(args[1], args[2], args[3])
                    
                    if result['success']:
                        console.print(f"[green]✅ Module '{result['module_name']}' created successfully[/green]")
                        console.print(f"[dim]📁 Path: {result['module_path']}[/dim]")
                    else:
                        console.print(f"[red]❌ Error: {result.get('error', result.get('message', 'Unknown error'))}[/red]")
                
                elif command == 'customize':
                    if len(parts) < 3:
                        console.print("[red]Usage: customize <module_path> <customization_request>[/red]")
                        continue
                    
                    result = self.customize_existing_module(parts[1], parts[2])
                    
                    if result['success']:
                        console.print(f"[green]✅ Module customized successfully[/green]")
                        console.print(f"[dim]📁 Path: {result['module_path']}[/dim]")
                        if result.get('analysis'):
                            console.print(Panel(Markdown(result['analysis']), title="📊 Customization Analysis"))
                    else:
                        console.print(f"[red]❌ Error: {result.get('error', result.get('message', 'Unknown error'))}[/red]")
                
                elif command == 'debug':
                    if len(parts) < 3:
                        console.print("[red]Usage: debug <error_message> <code_context> [module_path][/red]")
                        continue
                    
                    module_path = parts[3] if len(parts) > 3 else None
                    result = self.debug_odoo_issue(parts[1], parts[2], module_path)
                    
                    if result['success']:
                        console.print(f"[green]✅ Debug analysis completed[/green]")
                        if result.get('testing_instructions'):
                            console.print(Panel(Markdown(result['testing_instructions']), title="🧪 Testing Instructions"))
                    else:
                        console.print(f"[red]❌ Error: {result.get('error', result.get('message', 'Unknown error'))}[/red]")
                
                else:
                    console.print(f"[red]❌ Unknown command: {command}[/red]")
                    console.print("[dim]Type 'help' for available commands[/dim]")
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]👋 Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")
    
    def show_config(self):
        """Display current configuration"""
        config_table = Table(title="Current Configuration")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="green")
        
        config_table.add_row("Gemini API", "✅ Connected" if self.gemini_api_key else "❌ Not configured")
        config_table.add_row("Odoo Version", self.odoo_version)
        config_table.add_row("Addons Path", str(self.odoo_addons_path))
        config_table.add_row("Agent Mode", self.agent_mode)
        config_table.add_row("Auto Approve", "✅ Enabled" if self.auto_approve else "❌ Disabled")
        config_table.add_row("Backup Files", "✅ Enabled" if self.backup_files else "❌ Disabled")
        
        console.print(config_table)

def main():
    """Main function to run the Gemini Odoo agent"""
    try:
        agent = GeminiOdooAgent()
        agent.interactive_mode()
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Goodbye![/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Fatal error: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()