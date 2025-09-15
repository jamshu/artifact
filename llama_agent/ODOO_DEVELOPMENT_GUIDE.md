# Odoo 16 AI Development Agent - Complete Guide

## 🚀 Overview

This AI agent is specifically designed for Odoo 16 development, providing intelligent assistance for module creation, customization, debugging, and documentation generation.

## 📋 Best Models for Odoo Development

### **Primary Recommendations:**

1. **DeepSeek Coder 33B** (`deepseek-coder:33b`)
   - **Best for:** Complex Odoo module development, enterprise patterns
   - **Strengths:** Excellent Python knowledge, understands ORM patterns, good at inheritance
   - **Use when:** Creating complex modules, working with advanced features

2. **CodeLlama 34B** (`codellama:34b`)
   - **Best for:** Large codebase understanding, refactoring
   - **Strengths:** Strong at code analysis, debugging, architectural decisions
   - **Use when:** Analyzing existing modules, debugging complex issues

3. **Qwen2.5-Coder 7B** (`qwen2.5-coder:7b`)
   - **Best for:** Fast development, quick prototypes
   - **Strengths:** Fast response times, good code generation, efficient
   - **Use when:** Rapid prototyping, simple modules, quick fixes

### **Model Performance Comparison:**

| Model | Speed | Code Quality | Odoo Knowledge | Memory Usage |
|-------|-------|--------------|----------------|--------------|
| DeepSeek Coder 33B | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | High |
| CodeLlama 34B | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | High |
| Qwen2.5-Coder 7B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Medium |
| Llama3.2 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | Low |

## 🛠️ Installation and Setup

### 1. Install Required Models

```bash
# Install the best models for Odoo development
ollama pull deepseek-coder:33b    # Primary choice for complex development
ollama pull codellama:34b         # Great for debugging and analysis  
ollama pull qwen2.5-coder:7b      # Fast prototyping and simple tasks
ollama pull nomic-embed-text      # For embeddings and search
```

### 2. Set up the Agent

```bash
# Activate your virtual environment
source .venv/bin/activate

# Start the Odoo AI agent
python odoo_agent.py
```

## 💡 Usage Examples

### Creating a New Module

```bash
🔧 odoo-agent> create-module inventory_alerts "Inventory Alert System" "Low stock alerts, email notifications, dashboard widgets"
```

### Customizing Existing Module

```bash
🔧 odoo-agent> customize sale_management "Add custom approval workflow" "Multi-level approval for sales orders above $10000"
```

### Debugging Issues

```bash
🔧 odoo-agent> debug "AttributeError: 'sale.order' object has no attribute 'custom_field'" "class SaleOrder(models.Model): _inherit = 'sale.order'"
```

### Switch Models for Different Tasks

```bash
🔧 odoo-agent> switch-model qwen2.5-coder:7b    # For quick tasks
🔧 odoo-agent> switch-model deepseek-coder:33b  # For complex development
```

## 📚 Odoo 16 Development Best Practices

### Model Development

```python
# ✅ Good Example
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    # Proper field definition with help text
    custom_priority = fields.Selection([
        ('low', 'Low Priority'),
        ('high', 'High Priority')
    ], string='Priority Level', help='Product priority for inventory management')
    
    # Computed field with proper dependencies
    @api.depends('list_price', 'standard_price')
    def _compute_profit_margin(self):
        for product in self:
            if product.standard_price:
                product.profit_margin = (product.list_price - product.standard_price) / product.standard_price * 100
            else:
                product.profit_margin = 0.0
    
    profit_margin = fields.Float(
        string='Profit Margin (%)', 
        compute='_compute_profit_margin',
        store=True
    )
```

### View Development

```xml
<!-- ✅ Good Example -->
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_product_template_form_inherit" model="ir.ui.view">
        <field name="name">product.template.form.inherit</field>
        <field name="model">product.template</field>
        <field name="inherit_id" ref="product.product_template_form_view"/>
        <field name="arch" type="xml">
            <xpath expr="//field[@name='list_price']" position="after">
                <field name="custom_priority"/>
                <field name="profit_margin" readonly="1"/>
            </xpath>
        </field>
    </record>
</odoo>
```

### Security Rules

```csv
# ✅ Good Example - ir.model.access.csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_custom_model_user,custom.model.user,model_custom_model,base.group_user,1,0,0,0
access_custom_model_manager,custom.model.manager,model_custom_model,base.group_system,1,1,1,1
```

## 🎯 Development Workflows

### 1. New Module Creation Workflow

```
1. Plan module structure and dependencies
2. Use create-module command with detailed requirements
3. Review generated code structure
4. Add custom business logic
5. Create views and security rules
6. Test functionality
7. Generate documentation
```

### 2. Customization Workflow

```
1. Analyze existing module structure
2. Identify inheritance points
3. Use customize command for guidance
4. Implement inheritance patterns
5. Test backward compatibility
6. Document changes
```

### 3. Debugging Workflow

```
1. Reproduce the error
2. Gather error context and logs
3. Use debug command for analysis
4. Apply suggested fixes
5. Test solution
6. Document resolution
```

## 🔧 Configuration Tips

### For Development Environment

```python
# Use faster model for rapid development
config = OdooAgentConfig(
    ollama_model="qwen2.5-coder:7b",
    repository_path="/path/to/your/addons",
    chroma_db_path="./chroma_db"
)
```

### For Production-Quality Code

```python
# Use more powerful model for production code
config = OdooAgentConfig(
    ollama_model="deepseek-coder:33b",
    repository_path="/path/to/your/addons", 
    chroma_db_path="./chroma_db"
)
```

## 📊 Performance Optimization

### Model Selection Strategy

- **Development Phase:** `qwen2.5-coder:7b` for speed
- **Code Review:** `codellama:34b` for analysis
- **Production Code:** `deepseek-coder:33b` for quality
- **Documentation:** `llama3.2` for general text

### Memory Management

- Large models (33B+) require 16GB+ RAM
- Use model switching to optimize resource usage
- Close unused applications when running large models

## 🚨 Common Issues and Solutions

### Model Too Slow

```bash
# Switch to faster model
🔧 odoo-agent> switch-model qwen2.5-coder:7b
```

### Out of Memory

```bash
# Use smaller model or increase swap
🔧 odoo-agent> switch-model llama3.2
```

### Poor Code Quality

```bash
# Use more powerful model
🔧 odoo-agent> switch-model deepseek-coder:33b
```

## 📁 Project Structure

```
your_odoo_project/
├── addons/
│   ├── custom_module_1/
│   ├── custom_module_2/
│   └── ...
├── ai_agent/
│   ├── ai_agent.py
│   ├── odoo_agent.py
│   ├── chroma_db/
│   └── docs/
└── README.md
```

## 🎓 Advanced Features

### Code Analysis and Refactoring

The agent can analyze existing Odoo modules and suggest improvements:

```bash
🔧 odoo-agent> refactor models/sale_order.py
```

### Automated Documentation

Generate comprehensive documentation for your modules:

```bash
🔧 odoo-agent> doc models/product_template.py
```

### Repository Indexing

Index your entire addon repository for better context:

```bash
🔧 odoo-agent> index
```

## 🤝 Contributing

Feel free to extend the agent with:
- Additional Odoo-specific prompts
- Custom model configurations
- Industry-specific templates
- Integration with Odoo development tools

## 🏆 Success Tips

1. **Start Small:** Begin with simple modules using fast models
2. **Iterate Quickly:** Use the agent for rapid prototyping
3. **Review Carefully:** Always review AI-generated code
4. **Test Thoroughly:** Test all functionality before deployment
5. **Document Everything:** Use the agent to maintain documentation

---

## 🎯 Ready to Start?

```bash
# Start your Odoo development journey
python odoo_agent.py

# Create your first module
🔧 odoo-agent> create-module my_first_module "My First Odoo Module" "Basic CRUD operations with custom fields"
```

Happy Odoo coding! 🚀