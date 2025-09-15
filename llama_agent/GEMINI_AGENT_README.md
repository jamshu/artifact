# 🤖 Gemini-Powered Odoo 16 Development Agent

An advanced AI assistant that uses Google's Gemini 2.0 Flash model for intelligent Odoo development with interactive diff approval and a beautiful web interface.

## ✨ Features

### 🧠 **AI-Powered Development**
- **Code Analysis**: Deep analysis of existing Odoo code with improvement suggestions
- **Module Creation**: Generate complete, production-ready Odoo modules
- **Smart Customization**: Intelligent modification of existing modules
- **Advanced Debugging**: Root cause analysis and automated fixes

### 🎛️ **Interactive Interfaces**
- **Terminal Interface**: Rich CLI with colored diffs and interactive prompts
- **Web Interface**: Beautiful, responsive web UI for browser-based development
- **Diff Approval**: Review all changes before applying them
- **Real-time Feedback**: Live updates and progress indicators

### 🛡️ **Safety & Control**
- **Interactive Approval**: Review and approve/reject each change
- **Automatic Backups**: Create timestamped backups before modifications
- **File-by-file Review**: Approve changes individually
- **Edit-before-Apply**: Manually edit generated code before applying

## 🚀 Quick Start

### 1. **Setup Environment**

```bash
# Clone or navigate to your agent directory
cd /Users/jamshid/Desktop/artifact/llama_agent

# Ensure virtual environment is activated
source .venv/bin/activate

# Install required packages (already done)
# uv pip install google-generativeai python-dotenv rich flask flask-cors --python .venv/bin/python
```

### 2. **Configure Gemini API**

Edit the `.env` file with your Gemini API key:

```bash
# Edit .env file
nano .env
```

```env
# Gemini API Configuration
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Odoo Development Settings
ODOO_ADDONS_PATH=/Users/jamshid/Desktop/artifact/llama_agent/test_modules
ODOO_VERSION=16.0

# Agent Configuration
AGENT_MODE=development
AUTO_APPROVE_CHANGES=false
BACKUP_FILES=true

# Web UI Configuration
UI_HOST=localhost
UI_PORT=5000
UI_DEBUG=true
```

### 3. **Get Your Gemini API Key**

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API key"
3. Copy the generated key
4. Replace `your_actual_gemini_api_key_here` in the `.env` file

## 🎮 Usage Options

### Option 1: Terminal Interface

```bash
# Start the terminal-based agent
python gemini_odoo_agent.py
```

**Available Commands:**
- `analyze <file_path>` - Analyze existing code
- `create <module_name> <description> <features>` - Create new module
- `customize <module_path> <request>` - Customize existing module
- `debug <error> <context> [module_path]` - Debug issues
- `config` - Show configuration
- `help` - Show help
- `quit` - Exit

### Option 2: Web Interface

```bash
# Start the web UI
python web_ui.py
```

Then open your browser to: **http://localhost:5000**

## 💡 Usage Examples

### 📊 **Code Analysis**

**Terminal:**
```bash
🤖 gemini-agent> analyze models/product_template.py
```

**Web UI:**
1. Go to "Analyze Code" tab
2. Select file from dropdown
3. Click "🔍 Analyze Code"

### 🔧 **Create New Module**

**Terminal:**
```bash
🤖 gemini-agent> create inventory_alerts "Inventory Alert System" "Low stock alerts, email notifications, dashboard widgets"
```

**Web UI:**
1. Go to "Create Module" tab
2. Fill in module details
3. Click "🚀 Create Module"

### ⚙️ **Customize Module**

**Terminal:**
```bash
🤖 gemini-agent> customize ./test_modules/sample_inventory "Add barcode scanning functionality"
```

**Web UI:**
1. Go to "Customize Module" tab
2. Select module and describe customization
3. Click "⚡ Customize Module"

### 🐛 **Debug Issues**

**Terminal:**
```bash
🤖 gemini-agent> debug "AttributeError: 'sale.order' object has no attribute 'custom_field'" "class SaleOrder(models.Model): _inherit = 'sale.order'"
```

**Web UI:**
1. Go to "Debug Issue" tab
2. Paste error message and code context
3. Click "🔍 Debug Issue"

## 🎨 Interactive Diff Approval

The agent shows you exactly what changes it wants to make:

### **Change Preview**
```
📋 Create module: inventory_alerts
Proposed changes: 7 files

┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Action ┃ File                ┃ Description                                                  ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ CREATE │ __manifest__.py     │ Create __manifest__.py: Module manifest with dependencies   │
│ CREATE │ __init__.py         │ Create __init__.py: Module initialization                   │
│ CREATE │ models/__init__.py  │ Create models/__init__.py: Models initialization           │
│ CREATE │ models/alert.py     │ Create models/alert.py: Alert model definition             │
└────────┴─────────────────────┴──────────────────────────────────────────────────────────┘
```

### **Individual File Review**
```
📄 Change 1/7: __manifest__.py
Action: create | Path: /Users/jamshid/.../test_modules/inventory_alerts/__manifest__.py
Description: Create __manifest__.py: Module manifest with dependencies

📝 New file content:
{
    'name': 'Inventory Alert System',
    'version': '16.0.1.0.0',
    'summary': 'Low stock alerts and notifications',
    'description': '''
        Advanced inventory alert system with:
        - Low stock monitoring
        - Email notifications
        - Dashboard widgets
        - Configurable thresholds
    ''',
    ...
}

Action for __manifest__.py [approve/skip/edit/cancel]: approve
```

### **Diff View for Modifications**
```
🔄 File diff:
--- a/models/product_template.py
+++ b/models/product_template.py
@@ -15,6 +15,12 @@ class ProductTemplate(models.Model):
     last_inventory_date = fields.Datetime(
         string='Last Inventory Check'
     )
+    
+    alert_threshold = fields.Float(
+        string='Alert Threshold',
+        help='Stock level that triggers alert'
+    )
```

## ⚙️ Configuration Options

### **Environment Variables**

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | - | Your Gemini API key (**required**) |
| `ODOO_ADDONS_PATH` | `./test_modules` | Path to your Odoo addons |
| `ODOO_VERSION` | `16.0` | Target Odoo version |
| `AGENT_MODE` | `development` | Agent mode |
| `AUTO_APPROVE_CHANGES` | `false` | Skip interactive approval |
| `BACKUP_FILES` | `true` | Create backups before changes |
| `UI_HOST` | `localhost` | Web UI host |
| `UI_PORT` | `5000` | Web UI port |
| `UI_DEBUG` | `true` | Flask debug mode |

### **Safety Settings**

The agent uses conservative Gemini settings for code generation:

```python
generation_config = {
    temperature: 0.1,    # Low randomness for consistent code
    top_p: 0.8,         # Focus on high-probability tokens
    top_k: 40,          # Limit vocabulary for stability
    max_output_tokens: 8192  # Support large module generation
}
```

## 🔧 Advanced Features

### **Code Analysis Deep Dive**

The agent provides comprehensive analysis:

1. **Code Quality Assessment** (1-10 rating)
2. **Odoo Best Practices** compliance check
3. **Performance Issues** identification
4. **Security Concerns** highlighting
5. **Refactoring Suggestions** with examples
6. **Missing Features** recommendations

### **Smart Module Generation**

Creates complete, production-ready modules:

- ✅ **Complete file structure**
- ✅ **Proper Odoo 16 patterns**
- ✅ **Security rules and access rights**
- ✅ **Comprehensive views** (form, tree, search)
- ✅ **Sample data** when appropriate
- ✅ **Field validations** and constraints
- ✅ **Modern decorators** and APIs

### **Intelligent Customization**

Safely modifies existing modules:

- 🔍 **Analyzes existing code** structure
- 🧬 **Proper inheritance** patterns
- 🛡️ **Preserves existing** functionality
- 🔄 **Updates dependencies** as needed
- 📋 **Creates comprehensive** diffs

### **Advanced Debugging**

Provides expert-level debugging:

- 🎯 **Root cause analysis**
- 💡 **Solution strategies**
- 🔧 **Specific code fixes**
- 🛡️ **Prevention tips**
- 🧪 **Testing instructions**

## 🚨 Troubleshooting

### **Common Issues**

#### **Gemini API Key Not Working**
```bash
❌ Error: GEMINI_API_KEY not found in .env file
```
**Solution:** Ensure your API key is correctly set in the `.env` file.

#### **Module Not Found**
```bash
❌ Error: Module not found: /path/to/module
```
**Solution:** Check the `ODOO_ADDONS_PATH` in your `.env` file.

#### **Web UI Not Loading**
```bash
🚀 Starting Gemini Odoo Agent Web UI
📱 Access at: http://localhost:5000
```
**Solution:** Ensure Flask dependencies are installed and port 5000 is available.

### **Debug Mode**

Enable verbose logging:

```bash
# Set debug mode in .env
UI_DEBUG=true
AGENT_MODE=debug
```

## 🛡️ Best Practices

### **Development Workflow**

1. **Start Small**: Begin with simple modules
2. **Review Everything**: Always review generated code
3. **Test Thoroughly**: Test all functionality before deployment
4. **Use Backups**: Keep the backup feature enabled
5. **Iterative Development**: Make small, incremental changes

### **Security Guidelines**

- ✅ **Always review** security rules
- ✅ **Test access controls** thoroughly
- ✅ **Follow Odoo** security patterns
- ✅ **Validate user inputs** properly
- ✅ **Use proper** field constraints

### **Code Quality**

- ✅ **Follow PEP8** standards
- ✅ **Use proper** Odoo patterns
- ✅ **Add comprehensive** documentation
- ✅ **Include help text** for fields
- ✅ **Use descriptive** variable names

## 📊 Comparison with Local Models

| Feature | Gemini Agent | Local Ollama Agent |
|---------|-------------|-------------------|
| **Speed** | ⚡ Very Fast | 🐢 Slow (model dependent) |
| **Code Quality** | 🌟 Excellent | ⭐ Good (model dependent) |
| **Odoo Knowledge** | 🎯 Expert Level | 📚 Good |
| **Internet Required** | ✅ Yes | ❌ No |
| **Cost** | 💰 API costs | 🆓 Free |
| **Diff Approval** | ✅ Interactive | ✅ Interactive |
| **Web Interface** | ✅ Modern UI | ❌ Terminal only |

## 🎯 When to Use Each Mode

### **Use Terminal Interface When:**
- 🔧 **Quick development** tasks
- 🖥️ **Working in SSH/remote** environments  
- ⚡ **Minimal resource** requirements
- 🛠️ **Automation scripting**

### **Use Web Interface When:**
- 👥 **Team collaboration** needed
- 📱 **Better visualization** required
- 🎨 **Rich formatting** important
- 🖱️ **Point-and-click** preferred

## 🔮 Future Enhancements

### **Planned Features**
- 📊 **Visual diff viewer** with syntax highlighting
- 🔄 **Git integration** for version control
- 🧪 **Automated testing** generation
- 📈 **Performance profiling** 
- 🌐 **Multi-language support**
- 🔌 **Plugin system** for extensions

## 🤝 Contributing

Feel free to extend the agent with:
- 🎨 **UI improvements**
- 🧠 **Better prompts**
- 🔧 **New features**
- 🐛 **Bug fixes**
- 📚 **Documentation**

---

## 🎉 Ready to Start?

### **Quick Test:**

1. **Set up your API key** in `.env`
2. **Start the web interface**: `python web_ui.py`
3. **Open browser** to http://localhost:5000
4. **Create your first module**! 🚀

### **Example Module Creation:**

**Module Name:** `customer_portal`
**Description:** `Enhanced customer portal with advanced features`
**Features:** `Customer dashboard, order tracking, invoice downloads, support tickets`

The agent will generate a complete, working Odoo module with all necessary files, proper security, and best practices! ✨

---

**Happy Odoo Development with AI! 🤖✨**