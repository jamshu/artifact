#!/usr/bin/env python3

from odoo_agent import OdooAIAgent, OdooAgentConfig

def test_odoo_module_creation():
    """Test creating a sample Odoo module"""
    
    # Use a faster model for testing
    config = OdooAgentConfig(
        ollama_model="qwen2.5-coder:7b",  # Faster model for testing
        repository_path="./test_modules",
        chroma_db_path="./chroma_db"
    )
    
    agent = OdooAIAgent(config)
    
    print("🧪 Testing Odoo module creation...")
    
    # Test creating a simple CRM extension module
    result = agent.create_odoo_module(
        module_name="crm_lead_scoring",
        description="CRM Lead Scoring System - Automatically score leads based on various criteria",
        features="Lead scoring algorithm, custom fields for score display, automated workflows, reporting dashboard"
    )
    
    print(f"\n📋 Result: {result}")
    
    if result['success']:
        print(f"\n✅ Module created successfully!")
        print(f"📁 Module path: {result['module_path']}")
        print(f"📚 Guide file: {result['guide_file']}")
        
        # Show part of the generated content
        print(f"\n📄 Generated content preview:")
        print("=" * 60)
        print(result['response'][:1000] + "..." if len(result['response']) > 1000 else result['response'])
        print("=" * 60)
    else:
        print(f"❌ Module creation failed: {result.get('error')}")

if __name__ == "__main__":
    test_odoo_module_creation()