#!/usr/bin/env python3
"""
Odoo 16 Development AI Agent
Specialized for Odoo module creation, customization, and development
"""

import os
import sys
import json
from pathlib import Path
from ai_agent import AICodeAgent, AgentConfig
from langchain.prompts import PromptTemplate

class OdooAgentConfig(AgentConfig):
    """Odoo-specific agent configuration"""
    
    def __init__(self, **kwargs):
        # Set Odoo-specific defaults
        kwargs.setdefault('ollama_model', 'deepseek-coder:33b')  # Best for complex Odoo development
        kwargs.setdefault('supported_extensions', [
            '.py', '.xml', '.csv', '.yml', '.yaml', '.json', 
            '.js', '.css', '.scss', '.html', '.po', '.pot'
        ])
        super().__init__(**kwargs)

class OdooAIAgent(AICodeAgent):
    """Specialized AI Agent for Odoo 16 Development"""
    
    def __init__(self, config: OdooAgentConfig):
        super().__init__(config)
        self.setup_odoo_prompts()
    
    def setup_odoo_prompts(self):
        """Setup Odoo-specific prompt templates"""
        
        self.odoo_module_prompt = PromptTemplate(
            input_variables=["module_name", "description", "features"],
            template="""
You are an expert Odoo 16 developer. Create a complete Odoo module with the following specifications:

Module Name: {module_name}
Description: {description}
Required Features: {features}

Please create a complete module structure including:

1. **__manifest__.py** - Module manifest with proper dependencies and metadata
2. **models/__init__.py** and **models/[model_name].py** - Model definitions with fields, methods, and constraints
3. **views/[view_name].xml** - Views (form, tree, search) with proper actions and menus
4. **security/ir.model.access.csv** - Access rights and security rules
5. **data/[data_file].xml** - Initial data if needed
6. **__init__.py** - Module initialization

Follow Odoo 16 best practices:
- Use proper field types and attributes
- Include help text and labels
- Add proper constraints and validations
- Use appropriate view inheritance where needed
- Include proper security settings
- Follow PEP8 and Odoo coding guidelines
- Use proper module structure and naming conventions

Provide complete, working code for each file with detailed comments.
"""
        )
        
        self.odoo_customization_prompt = PromptTemplate(
            input_variables=["base_module", "customization", "requirements"],
            template="""
You are an expert Odoo 16 developer. Create a customization for the following:

Base Module: {base_module}
Customization Required: {customization}
Specific Requirements: {requirements}

Please provide:

1. **Inheritance approach** - Explain whether to use model inheritance, view inheritance, or both
2. **Code implementation** - Complete Python code with proper inheritance
3. **View modifications** - XML views with proper inheritance and xpath
4. **Security considerations** - Any additional security rules needed
5. **Data migration** - Any data changes or migration scripts if needed

Follow Odoo 16 best practices:
- Use proper inheritance patterns (_inherit vs _name)
- Preserve existing functionality
- Add comprehensive logging and error handling
- Include proper field dependencies and computed fields
- Use appropriate decorators (@api.depends, @api.constrains, etc.)
- Follow upgrade-safe practices

Provide complete, working code with detailed explanations.
"""
        )
        
        self.odoo_debug_prompt = PromptTemplate(
            input_variables=["error_message", "code_context", "odoo_version"],
            template="""
You are an expert Odoo 16 debugger. Analyze and fix the following error:

Error Message: {error_message}
Code Context: {code_context}
Odoo Version: {odoo_version}

Please provide:

1. **Root Cause Analysis** - Explain what's causing the error
2. **Solution** - Complete fixed code
3. **Prevention** - How to avoid similar issues in the future
4. **Testing** - How to test the fix
5. **Best Practices** - Related Odoo development best practices

Common Odoo 16 considerations:
- Field definitions and ORM usage
- View inheritance and XML structure
- Security and access rights
- Module dependencies and loading order
- API changes from previous versions
- Performance implications

Provide detailed, step-by-step solutions.
"""
        )
    
    def create_odoo_module(self, module_name: str, description: str, features: str) -> dict:
        """Create a complete Odoo module"""
        try:
            prompt = self.odoo_module_prompt.format(
                module_name=module_name,
                description=description,
                features=features
            )
            
            response = self.llm.invoke(prompt)
            
            # Create module directory structure
            module_path = Path(self.config.repository_path) / module_name
            module_path.mkdir(exist_ok=True)
            
            # Create subdirectories
            for subdir in ['models', 'views', 'security', 'data', 'static/description']:
                (module_path / subdir).mkdir(parents=True, exist_ok=True)
            
            # Save the response as a development guide
            guide_path = module_path / 'DEVELOPMENT_GUIDE.md'
            with open(guide_path, 'w') as f:
                f.write(f"# {module_name} - Development Guide\n\n")
                f.write(f"**Description:** {description}\n\n")
                f.write(f"**Features:** {features}\n\n")
                f.write("## AI-Generated Code\n\n")
                f.write(response)
            
            return {
                'success': True,
                'module_path': str(module_path),
                'guide_file': str(guide_path),
                'response': response
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def customize_odoo_module(self, base_module: str, customization: str, requirements: str = "") -> dict:
        """Create customization for existing Odoo module"""
        try:
            prompt = self.odoo_customization_prompt.format(
                base_module=base_module,
                customization=customization,
                requirements=requirements
            )
            
            response = self.llm.invoke(prompt)
            
            # Create customization directory
            custom_module_name = f"{base_module}_custom"
            module_path = Path(self.config.repository_path) / custom_module_name
            module_path.mkdir(exist_ok=True)
            
            # Save customization guide
            guide_path = module_path / 'CUSTOMIZATION_GUIDE.md'
            with open(guide_path, 'w') as f:
                f.write(f"# {base_module} Customization Guide\n\n")
                f.write(f"**Base Module:** {base_module}\n")
                f.write(f"**Customization:** {customization}\n")
                f.write(f"**Requirements:** {requirements}\n\n")
                f.write("## Implementation Details\n\n")
                f.write(response)
            
            return {
                'success': True,
                'module_path': str(module_path),
                'guide_file': str(guide_path),
                'response': response
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def debug_odoo_issue(self, error_message: str, code_context: str, odoo_version: str = "16.0") -> dict:
        """Debug Odoo-specific issues"""
        try:
            prompt = self.odoo_debug_prompt.format(
                error_message=error_message,
                code_context=code_context,
                odoo_version=odoo_version
            )
            
            response = self.llm.invoke(prompt)
            
            # Save debug analysis
            debug_path = Path(self.config.repository_path) / 'DEBUG_ANALYSIS.md'
            with open(debug_path, 'w') as f:
                f.write("# Odoo Debug Analysis\n\n")
                f.write(f"**Error:** {error_message}\n\n")
                f.write(f"**Odoo Version:** {odoo_version}\n\n")
                f.write("## Analysis and Solution\n\n")
                f.write(response)
            
            return {
                'success': True,
                'debug_file': str(debug_path),
                'response': response
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def interactive_mode(self):
        """Odoo-specific interactive mode"""
        print("🚀 Odoo 16 Development AI Agent")
        print("=" * 50)
        print("Available commands:")
        print("  create-module <name> <description> <features> - Create new Odoo module")
        print("  customize <base_module> <customization> - Customize existing module")
        print("  debug <error_message> <code_context> - Debug Odoo issues")
        print("  index - Index the repository")
        print("  refactor <file_path> - Refactor code")
        print("  doc <file_path> - Generate documentation")
        print("  search <query> - Search in codebase")
        print("  shell <command> - Execute shell command")
        print("  switch-model <model_name> - Switch to different model")
        print("  quit - Exit")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n🔧 odoo-agent> ").strip()
                
                if not user_input:
                    continue
                
                parts = user_input.split(' ', 3)
                command = parts[0].lower()
                
                if command == 'quit':
                    break
                elif command == 'create-module':
                    if len(parts) >= 4:
                        name, description, features = parts[1], parts[2], parts[3]
                        result = self.create_odoo_module(name, description, features)
                        print(json.dumps(result, indent=2))
                    else:
                        print("Usage: create-module <name> <description> <features>")
                elif command == 'customize':
                    if len(parts) >= 3:
                        base_module, customization = parts[1], parts[2]
                        requirements = parts[3] if len(parts) > 3 else ""
                        result = self.customize_odoo_module(base_module, customization, requirements)
                        print(json.dumps(result, indent=2))
                    else:
                        print("Usage: customize <base_module> <customization> [requirements]")
                elif command == 'debug':
                    if len(parts) >= 3:
                        error_message, code_context = parts[1], parts[2]
                        result = self.debug_odoo_issue(error_message, code_context)
                        print(json.dumps(result, indent=2))
                    else:
                        print("Usage: debug <error_message> <code_context>")
                elif command == 'switch-model':
                    if len(parts) >= 2:
                        model_name = parts[1]
                        self.switch_model(model_name)
                        print(f"Switched to model: {model_name}")
                    else:
                        print("Usage: switch-model <model_name>")
                        print("Available models: deepseek-coder:33b, codellama:34b, qwen2.5-coder:7b")
                elif command == 'index':
                    self.index_repository()
                elif command == 'refactor' and len(parts) >= 2:
                    result = self.refactor_code(parts[1])
                    print(json.dumps(result, indent=2))
                elif command == 'doc' and len(parts) >= 2:
                    result = self.generate_documentation(parts[1])
                    print(json.dumps(result, indent=2))
                elif command == 'search' and len(parts) >= 2:
                    results = self.vector_store.search(parts[1])
                    for i, result in enumerate(results):
                        print(f"\nResult {i+1}:")
                        print(f"File: {result['metadata']['file_path']}")
                        print(f"Content: {result['content'][:200]}...")
                elif command == 'shell' and len(parts) >= 2:
                    result = self.execute_command(parts[1])
                    print(json.dumps(result, indent=2))
                else:
                    print(f"Unknown command: {command}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("👋 Happy Odoo coding!")
    
    def switch_model(self, model_name: str):
        """Switch to a different model"""
        from langchain_ollama import OllamaLLM
        self.config.ollama_model = model_name
        self.llm = OllamaLLM(
            model=model_name,
            base_url=self.config.ollama_url
        )

def main():
    """Main function for Odoo AI Agent"""
    
    # Configuration
    config = OdooAgentConfig(
        repository_path="./",  # Change to your Odoo addons path
        chroma_db_path="./chroma_db"
    )
    
    # Initialize Odoo agent
    agent = OdooAIAgent(config)
    
    # Run in interactive mode
    agent.interactive_mode()

if __name__ == "__main__":
    main()