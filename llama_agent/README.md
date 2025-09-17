# 🤖 LangChain-Powered Odoo Development Agent

An advanced AI-powered assistant for Odoo development that uses LangChain for modular LLM support, enabling easy switching between different language models.

## ✨ Features

- 🔄 **Multi-LLM Support**: Switch between Gemini, OpenAI, and Anthropic models
- 📋 **Structured Prompts**: LangChain PromptTemplates for consistent, maintainable prompts
- 🌐 **Web Interface**: Clean, responsive web UI with real-time updates
- 📱 **CLI Interface**: Command-line interface for direct terminal usage
- 🔧 **Module Creation**: Generate complete Odoo modules with best practices
- ⚙️ **Module Customization**: Modify existing modules intelligently
- 📊 **Code Analysis**: Comprehensive code quality and security analysis
- 🐛 **Debug Assistant**: AI-powered debugging with suggested fixes
- 🔒 **Interactive Approval**: Review all changes before applying
- 📦 **File Backup**: Automatic backup of modified files
- 🎯 **Odoo-Specific**: Tailored for Odoo 15/16 development patterns

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- UV package manager
- Odoo development environment
- API key for your preferred LLM provider

### Installation

1. **Clone and setup the project:**
   ```bash
   cd /path/to/your/workspace
   git clone <your-repo> llama_agent
   cd llama_agent
   ```

2. **Install dependencies with UV:**
   ```bash
   uv sync
   ```

3. **Configure environment:**
   Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   ```

4. **Edit `.env` file:**
   ```env
   # LLM Configuration
   LLM_PROVIDER=gemini  # Options: gemini, openai, anthropic
   LLM_TEMPERATURE=0.1
   LLM_MAX_TOKENS=16384

   # Gemini API Configuration
   GEMINI_API_KEY=your_gemini_api_key_here

   # OpenAI API Configuration (optional)
   # OPENAI_API_KEY=your_openai_api_key_here
   # OPENAI_MODEL=gpt-4

   # Anthropic API Configuration (optional)
   # ANTHROPIC_API_KEY=your_anthropic_api_key_here
   # ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

   # Odoo Development Settings
   ODOO_ADDONS_PATH=/path/to/your/odoo/addons
   ODOO_VERSION=16.0

   # Agent Configuration
   AGENT_MODE=development
   AUTO_APPROVE_CHANGES=false
   BACKUP_FILES=true
   ```

## 🎮 Usage

### Web Interface

Start the web server:
```bash
uv run python web_ui.py
```

Then open http://localhost:8080 in your browser.

**Web UI Features:**
- 🔧 **Create Module Tab**: Generate new Odoo modules
- ⚙️ **Customize Module Tab**: Modify existing modules
- 📊 **Analyze Code Tab**: Get detailed code analysis
- 🐛 **Debug Issue Tab**: AI-powered debugging assistance

### CLI Interface

Run the command-line interface:
```bash
uv run python langchain_odoo_agent.py
```

**CLI Options:**
1. 🔍 Analyze existing code
2. 🔧 Create new module
3. ⚙️ Customize existing module
4. 🐛 Debug Odoo issue
5. ❌ Exit

## 🔄 Switching Between LLM Providers

### Gemini (Default)
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
```

### OpenAI
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo
```

### Anthropic
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

## 🏗️ Architecture

### Core Components

1. **`llm_config.py`** - LLM provider management and configuration
2. **`prompts.py`** - Structured prompt templates using LangChain
3. **`langchain_odoo_agent.py`** - Main agent logic with LangChain integration
4. **`web_ui.py`** - Flask-based web interface
5. **`templates/index.html`** - Responsive web UI with Alpine.js

### LangChain Integration

```python
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from llm_config import LLMConfig
from prompts import get_prompt_template

# Initialize LLM
llm_config = LLMConfig(provider="gemini")
llm = llm_config.get_llm()

# Get prompt template
prompt_template = get_prompt_template("module_creation")

# Create chain
chain = prompt_template | llm | str_parser

# Execute
response = chain.invoke({
    "odoo_version": "16.0",
    "module_name": "my_module",
    "description": "My custom module",
    "features": "Custom functionality"
})
```

### Prompt Templates

All prompts are now managed as LangChain `PromptTemplate` objects:

- **`CODE_ANALYSIS_TEMPLATE`** - For code quality analysis
- **`MODULE_CREATION_TEMPLATE`** - For generating new modules
- **`MODULE_CUSTOMIZATION_TEMPLATE`** - For modifying existing modules
- **`DEBUG_ISSUE_TEMPLATE`** - For debugging assistance

## 📝 Configuration Options

### Environment Variables

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `LLM_PROVIDER` | LLM provider to use | `gemini` | `gemini`, `openai`, `anthropic` |
| `LLM_TEMPERATURE` | Model temperature | `0.1` | `0.0` - `2.0` |
| `LLM_MAX_TOKENS` | Maximum output tokens | `16384` | Model-dependent |
| `ODOO_ADDONS_PATH` | Path to Odoo addons | `/opt/odoo/addons` | Valid directory path |
| `ODOO_VERSION` | Target Odoo version | `16.0` | `15.0`, `16.0`, `17.0` |
| `AUTO_APPROVE_CHANGES` | Skip change approval | `false` | `true`, `false` |
| `BACKUP_FILES` | Create file backups | `true` | `true`, `false` |

### Web UI Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `UI_HOST` | Web server host | `localhost` |
| `UI_PORT` | Web server port | `8080` |
| `UI_DEBUG` | Flask debug mode | `true` |

## 🔧 Development

### Project Structure

```
llama_agent/
├── llm_config.py           # LLM provider configuration
├── prompts.py              # LangChain prompt templates
├── langchain_odoo_agent.py # Main agent with LangChain
├── web_ui.py               # Flask web interface
├── templates/
│   └── index.html          # Web UI template
├── pyproject.toml          # UV project configuration
├── .env                    # Environment configuration
├── .env.example            # Environment template
└── README.md               # This file
```

### Adding New LLM Providers

1. **Update `LLMProvider` enum** in `llm_config.py`:
   ```python
   class LLMProvider(Enum):
       GEMINI = "gemini"
       OPENAI = "openai"
       ANTHROPIC = "anthropic"
       NEW_PROVIDER = "new_provider"  # Add here
   ```

2. **Add provider method** in `LLMConfig` class:
   ```python
   def _get_new_provider_llm(self) -> BaseLLM:
       api_key = os.getenv("NEW_PROVIDER_API_KEY")
       if not api_key:
           raise ValueError("NEW_PROVIDER_API_KEY not found")
       
       return NewProviderLLM(
           api_key=api_key,
           temperature=self.temperature,
           max_tokens=self.max_tokens
       )
   ```

3. **Update `get_llm()` method** to handle the new provider.

### Adding New Prompt Templates

1. **Define the template** in `prompts.py`:
   ```python
   NEW_TEMPLATE = PromptTemplate(
       input_variables=["param1", "param2"],
       template="""Your prompt template here with {param1} and {param2}"""
   )
   ```

2. **Register in `get_prompt_template()`** function.

3. **Use in agent methods**:
   ```python
   prompt_template = get_prompt_template("new_template")
   chain = prompt_template | self.llm | self.str_parser
   response = chain.invoke({"param1": value1, "param2": value2})
   ```

## 🧪 Testing

### Test Module Creation
```bash
# CLI
uv run python langchain_odoo_agent.py

# Web UI
uv run python web_ui.py
# Then visit http://localhost:8080
```

### Test Different Providers

1. **Test with Gemini:**
   ```bash
   export LLM_PROVIDER=gemini
   uv run python langchain_odoo_agent.py
   ```

2. **Test with OpenAI:**
   ```bash
   export LLM_PROVIDER=openai
   export OPENAI_API_KEY=your_key
   uv run python langchain_odoo_agent.py
   ```

3. **Test with Anthropic:**
   ```bash
   export LLM_PROVIDER=anthropic
   export ANTHROPIC_API_KEY=your_key
   uv run python langchain_odoo_agent.py
   ```

## 🚨 Troubleshooting

### Common Issues

1. **"LLM provider not found"**
   - Check `LLM_PROVIDER` value in `.env`
   - Ensure the provider's API key is configured

2. **"Failed to parse JSON response"**
   - LLM response may be truncated
   - Try increasing `LLM_MAX_TOKENS`
   - Check LLM provider rate limits

3. **"Module path not found"**
   - Verify `ODOO_ADDONS_PATH` points to correct directory
   - Ensure path permissions are correct

4. **Web UI not loading**
   - Check if port 8080 is available
   - Try changing `UI_PORT` in `.env`
   - Check firewall settings

### Debug Mode

Enable detailed logging:
```bash
export UI_DEBUG=true
uv run python web_ui.py
```

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your changes with tests
4. Submit a pull request

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review the LangChain documentation for advanced usage

---

**Happy Odoo Development! 🎉**