/**
 * Toon-enabled prompt templates for Odoo operations
 * These templates instruct the LLM to respond in Toon format for maximum token efficiency
 */

/**
 * Base Toon format instruction to include in all prompts
 */
const TOON_FORMAT_INSTRUCTION = `
CRITICAL FORMAT REQUIREMENT: You MUST respond using Toon format (Token-Oriented Object Notation) for maximum token efficiency.

Toon format rules:
1. For arrays of objects with uniform structure, use: arrayName[count]{field1,field2,field3}:
2. Follow with rows of comma-separated values
3. For multi-line string fields (like file content), use proper escaping or base64 if needed
4. Keep the format compact and efficient

Example Toon format:
files[3]{path,content,description}:
 __manifest__.py,# -*- coding: utf-8 -*-\\n{'name': 'Module'},Manifest file
 __init__.py,from . import models,Init file
 models/__init__.py,from . import product,Models init

For nested structures, you can use multiple Toon arrays or combine with minimal JSON where necessary.
`;

/**
 * Module Creation Template
 */
export const MODULE_CREATION_TEMPLATE = `You are an expert Odoo {odooVersion} developer specializing in creating production-ready modules.

${TOON_FORMAT_INSTRUCTION}

Task: Create a complete Odoo module with the following specifications:

Module Name: {moduleName}
Description: {description}
Required Features: {features}

Generate a complete module structure including:
1. __manifest__.py with proper metadata, dependencies, and data files
2. __init__.py files for package initialization
3. models/ directory with Python ORM models (proper inheritance, fields, constraints, computed fields)
4. views/ directory with XML views (form, tree, search, menu actions)
5. security/ir.model.access.csv with appropriate access rights
6. data/ directory if demo/default data is needed

Follow Odoo {odooVersion} best practices:
- Use proper model inheritance (_inherit or _name)
- Include help text for fields
- Add proper constraints and validation
- Use @api.depends for computed fields
- Follow naming conventions (snake_case for Python, dot.notation for XML IDs)
- Include security rules for all models

Respond in Toon format with this structure:
module_info{name,description,version,category}:
 {moduleName},{description},16.0.1.0.0,Custom

files[N]{path,content,description}:
 __manifest__.py,<full file content>,Module manifest
 __init__.py,<full file content>,Root init
 models/__init__.py,<full file content>,Models init
 ...

Ensure ALL file contents are complete and ready to use without modifications.`;

/**
 * Module Customization Template
 */
export const MODULE_CUSTOMIZATION_TEMPLATE = `You are an expert Odoo {odooVersion} developer specializing in module customization through inheritance.

${TOON_FORMAT_INSTRUCTION}

Task: Customize an existing Odoo module with the following request:

Module Path: {modulePath}
Customization Request: {customizationRequest}

Existing Module Structure:
{existingStructure}

Relevant File Contents:
{fileContents}

Create or modify files to implement the requested customization. Use proper Odoo inheritance patterns:
- Model inheritance: _inherit for extending existing models
- View inheritance: XPath expressions with proper position attributes (after, before, replace, inside, attributes)
- Workflow modifications: Proper state transitions and constraints

Follow best practices:
- Don't override core functionality unnecessarily
- Use inheritance instead of direct modification
- Maintain backwards compatibility
- Add proper comments explaining customizations
- Include security rules for new fields/models

Respond in Toon format:
analysis{current_structure,required_changes,approach}:
 <current structure summary>,<what needs to change>,<inheritance strategy>

files[N]{path,action,content,description}:
 models/sale_order.py,modify,<full file content>,Add custom fields to sale.order
 views/sale_order_views.xml,create,<full file content>,Custom sale order view
 ...

Where action is one of: create, modify, delete`;

/**
 * Debug Issue Template
 */
export const DEBUG_ISSUE_TEMPLATE = `You are an expert Odoo {odooVersion} developer and debugger.

${TOON_FORMAT_INSTRUCTION}

Task: Diagnose and fix an Odoo issue with the following details:

Error Message:
{errorMessage}

Code Context:
{codeContext}

Module Path: {modulePath}

Analyze the issue and provide:
1. Root cause analysis
2. Explanation of why the error occurred
3. Specific fixes with code changes
4. Testing instructions
5. Prevention tips for similar issues

Common Odoo issues to check:
- Missing model/field definitions
- Incorrect inheritance syntax
- Missing dependencies in __manifest__.py
- Access rights issues
- Invalid XML structure in views
- Python syntax errors in models
- Missing @api decorators
- Circular dependencies

Respond in Toon format:
diagnosis{error_type,root_cause,severity}:
 {errorType},{rootCause},high

solution{approach,explanation}:
 {approach},{explanation}

fixes[N]{file_path,action,content,explanation}:
 models/model.py,modify,<fixed code>,Add missing field definition
 __manifest__.py,modify,<updated manifest>,Add missing dependency
 ...

testing_steps[N]{step,command,expected_result}:
 1,Restart Odoo server,No errors in logs
 2,Update module,Module updates successfully
 3,Test functionality,Feature works as expected

prevention_tips[N]{tip}:
 Always declare fields before using them
 Check dependencies in manifest
 Test module updates before deployment`;

/**
 * Code Analysis Template
 */
export const CODE_ANALYSIS_TEMPLATE = `You are an expert Odoo {odooVersion} code reviewer.

${TOON_FORMAT_INSTRUCTION}

Task: Analyze the following Odoo code for quality, best practices, and potential issues:

File Path: {filePath}
Code:
{code}

Analyze for:
1. Odoo best practices compliance
2. Security vulnerabilities (SQL injection, XSS, access control)
3. Performance issues (N+1 queries, inefficient searches)
4. Code quality (readability, maintainability)
5. Missing functionality (constraints, validations, indexes)

Respond in Toon format:
summary{overall_quality,main_issues,recommendation}:
 {quality_score}/10,{issue_count} issues found,{overall_recommendation}

issues[N]{severity,category,line,description,suggestion}:
 high,security,45,SQL injection vulnerability,Use ORM methods instead of raw SQL
 medium,performance,67,N+1 query problem,Use read_group or computed field
 low,style,12,Missing docstring,Add function documentation

best_practices[N]{practice,current_status,recommendation}:
 Field validation,Missing,Add @api.constrains decorator
 Access control,Incomplete,Define proper security rules
 Error handling,Good,Continue current approach

security_concerns[N]{concern,risk_level,mitigation}:
 User input not sanitized,High,Use Odoo ORM and avoid raw queries
 Missing access rights check,Medium,Add proper @api.model decorators`;

/**
 * Format a prompt template with variables
 * @param {string} template - Template string with {variable} placeholders
 * @param {object} variables - Object with variable values
 * @returns {string} Formatted prompt
 */
export function formatPrompt(template, variables) {
  let formatted = template;

  for (const [key, value] of Object.entries(variables)) {
    const regex = new RegExp(`\\{${key}\\}`, 'g');
    formatted = formatted.replace(regex, value || '');
  }

  return formatted;
}

/**
 * Get prompt for module creation
 */
export function getModuleCreationPrompt(moduleName, description, features, odooVersion = '16.0') {
  return formatPrompt(MODULE_CREATION_TEMPLATE, {
    moduleName,
    description,
    features,
    odooVersion
  });
}

/**
 * Get prompt for module customization
 */
export function getModuleCustomizationPrompt(modulePath, customizationRequest, existingStructure, fileContents, odooVersion = '16.0') {
  return formatPrompt(MODULE_CUSTOMIZATION_TEMPLATE, {
    modulePath,
    customizationRequest,
    existingStructure,
    fileContents,
    odooVersion
  });
}

/**
 * Get prompt for debugging
 */
export function getDebugIssuePrompt(errorMessage, codeContext, modulePath, odooVersion = '16.0') {
  return formatPrompt(DEBUG_ISSUE_TEMPLATE, {
    errorMessage,
    codeContext,
    modulePath: modulePath || 'Not specified',
    odooVersion
  });
}

/**
 * Get prompt for code analysis
 */
export function getCodeAnalysisPrompt(filePath, code, odooVersion = '16.0') {
  return formatPrompt(CODE_ANALYSIS_TEMPLATE, {
    filePath,
    code,
    odooVersion
  });
}
