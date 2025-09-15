#!/usr/bin/env python3
"""
Prompt Templates for Odoo Agent
Using LangChain PromptTemplate for structured prompts
"""

from langchain_core.prompts import PromptTemplate


# Code Analysis Template
CODE_ANALYSIS_TEMPLATE = PromptTemplate(
    input_variables=["odoo_version", "file_path", "code_content"],
    template="""You are an expert Odoo {odoo_version} developer. Analyze the following code and provide detailed feedback:

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

Provide actionable suggestions with code examples."""
)


# Module Creation Template
MODULE_CREATION_TEMPLATE = PromptTemplate(
    input_variables=["odoo_version", "module_name", "description", "features"],
    template="""You are an expert Odoo {odoo_version} developer. Create a complete, production-ready Odoo module:

**Module Details:**
- Name: {module_name}
- Description: {description}
- Features: {features}
- Odoo Version: {odoo_version}

**Requirements:**
1. Create a complete module structure with all necessary files
2. Follow Odoo {odoo_version} best practices and coding standards
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
- Escape special characters properly (\\n, \\", \\\\)
- Keep file content concise but complete
- Ensure the JSON is valid and properly closed
- Do not include any text outside the JSON structure"""
)


# Module Customization Template
MODULE_CUSTOMIZATION_TEMPLATE = PromptTemplate(
    input_variables=["odoo_version", "customization_request", "existing_files"],
    template="""You are an expert Odoo {odoo_version} developer. Analyze the existing module and implement the requested customization:

**Customization Request:** {customization_request}

**Existing Module Files:**
{existing_files}

**Requirements:**
1. Analyze the existing code structure
2. Implement the requested customization following Odoo best practices
3. Preserve existing functionality
4. Add proper inheritance where needed
5. Update or create necessary views
6. Add security rules if needed
7. Update the manifest if new dependencies are required

**Provide response as JSON:**
```json
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
```

Only include files that need to be modified or created. For modifications, provide the complete new file content."""
)


# Debug Issue Template
DEBUG_ISSUE_TEMPLATE = PromptTemplate(
    input_variables=["odoo_version", "error_message", "code_context", "context_info"],
    template="""You are an expert Odoo {odoo_version} debugger. Analyze and fix the following issue:

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
```json
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
```"""
)


# Simple Analysis Template (for non-JSON responses)
SIMPLE_ANALYSIS_TEMPLATE = PromptTemplate(
    input_variables=["odoo_version", "request", "context"],
    template="""You are an expert Odoo {odoo_version} developer. 

**Request:** {request}
**Context:** {context}

Provide a comprehensive analysis and recommendations following Odoo best practices."""
)


def get_prompt_template(template_name: str) -> PromptTemplate:
    """Get a prompt template by name"""
    templates = {
        "code_analysis": CODE_ANALYSIS_TEMPLATE,
        "module_creation": MODULE_CREATION_TEMPLATE,
        "module_customization": MODULE_CUSTOMIZATION_TEMPLATE,
        "debug_issue": DEBUG_ISSUE_TEMPLATE,
        "simple_analysis": SIMPLE_ANALYSIS_TEMPLATE
    }
    
    if template_name not in templates:
        raise ValueError(f"Unknown template: {template_name}. Available: {list(templates.keys())}")
    
    return templates[template_name]