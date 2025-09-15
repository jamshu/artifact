#!/usr/bin/env python3
"""
Web UI for Gemini-Powered Odoo Agent
Browser-based interface for interactive development and diff approval
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from langchain_odoo_agent import LangChainOdooAgent, FileChange

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize the agent
agent = None

def init_agent():
    global agent
    if agent is None:
        agent = LangChainOdooAgent()

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/api/config')
def get_config():
    """Get agent configuration"""
    init_agent()
    provider_info = agent.get_provider_info()
    return jsonify({
        'odoo_version': agent.odoo_version,
        'addons_path': str(agent.odoo_addons_path),
        'agent_mode': agent.agent_mode,
        'auto_approve': agent.auto_approve,
        'backup_files': agent.backup_files,
        'llm_provider': provider_info['provider'],
        'llm_model': provider_info['model'],
        'llm_temperature': provider_info['temperature']
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_code():
    """Analyze existing code"""
    init_agent()
    data = request.json
    file_path = data.get('file_path')
    
    if not file_path:
        return jsonify({'success': False, 'error': 'file_path is required'})
    
    result = agent.analyze_existing_code(file_path)
    return jsonify(result)

@app.route('/api/create-module', methods=['POST'])
def create_module():
    """Create new Odoo module"""
    init_agent()
    data = request.json
    
    module_name = data.get('module_name')
    description = data.get('description')
    features = data.get('features')
    
    if not all([module_name, description, features]):
        return jsonify({'success': False, 'error': 'module_name, description, and features are required'})
    
    # Temporarily disable interactive approval for web UI
    agent.auto_approve = True
    result = agent.create_odoo_module(module_name, description, features)
    agent.auto_approve = False
    
    return jsonify(result)

@app.route('/api/customize-module', methods=['POST'])
def customize_module():
    """Customize existing module"""
    init_agent()
    data = request.json
    
    module_path = data.get('module_path')
    customization_request = data.get('customization_request')
    
    if not all([module_path, customization_request]):
        return jsonify({'success': False, 'error': 'module_path and customization_request are required'})
    
    # For web UI, we'll return the proposed changes for approval
    result = agent.customize_existing_module(module_path, customization_request)
    return jsonify(result)

@app.route('/api/debug', methods=['POST'])
def debug_issue():
    """Debug Odoo issue"""
    init_agent()
    data = request.json
    
    error_message = data.get('error_message')
    code_context = data.get('code_context')
    module_path = data.get('module_path')
    
    if not all([error_message, code_context]):
        return jsonify({'success': False, 'error': 'error_message and code_context are required'})
    
    result = agent.debug_odoo_issue(error_message, code_context, module_path)
    return jsonify(result)

@app.route('/api/list-modules')
def list_modules():
    """List available modules"""
    init_agent()
    modules = []
    
    if agent.odoo_addons_path.exists():
        for item in agent.odoo_addons_path.iterdir():
            if item.is_dir() and (item / '__manifest__.py').exists():
                modules.append({
                    'name': item.name,
                    'path': str(item),
                    'manifest_exists': True
                })
    
    return jsonify({'modules': modules})

@app.route('/api/module-files/<path:module_name>')
def get_module_files(module_name):
    """Get files in a module"""
    init_agent()
    module_path = agent.odoo_addons_path / module_name
    
    if not module_path.exists():
        return jsonify({'success': False, 'error': 'Module not found'})
    
    files = []
    for file_path in module_path.rglob('*'):
        if file_path.is_file() and file_path.suffix in ['.py', '.xml', '.csv', '.yml', '.yaml']:
            relative_path = file_path.relative_to(module_path)
            files.append({
                'path': str(relative_path),
                'full_path': str(file_path),
                'type': file_path.suffix,
                'size': file_path.stat().st_size
            })
    
    return jsonify({'files': files})

@app.route('/api/file-content')
def get_file_content():
    """Get content of a specific file"""
    file_path = request.args.get('path')
    
    if not file_path:
        return jsonify({'success': False, 'error': 'path parameter is required'})
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'success': True, 'content': content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/templates/<path:filename>')
def serve_templates(filename):
    """Serve template files"""
    return send_from_directory('templates', filename)

def create_templates():
    """Create HTML templates for the web UI"""
    # Templates are now managed separately in templates/ directory
    pass

def main():
    """Run the web UI"""
    create_templates()
    
    host = os.getenv('UI_HOST', 'localhost')
    port = int(os.getenv('UI_PORT', 5000))
    debug = os.getenv('UI_DEBUG', 'true').lower() == 'true'
    
    print(f"🚀 Starting Gemini Odoo Agent Web UI")
    print(f"📱 Access at: http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()