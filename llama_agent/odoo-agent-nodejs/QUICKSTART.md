# Quick Start Guide

Get up and running with Odoo Agent in 5 minutes!

## Step 1: Install Dependencies (1 minute)

```bash
cd odoo-agent-nodejs
npm install
```

## Step 2: Configure API Key (2 minutes)

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
nano .env
```

Choose ONE provider and add its API key:

### Option A: Gemini (Recommended - Free tier available)
```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your key: https://makersuite.google.com/app/apikey

### Option B: OpenAI
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key_here
```

Get your key: https://platform.openai.com/api-keys

### Option C: Anthropic
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_key_here
```

Get your key: https://console.anthropic.com/

## Step 3: Test It! (2 minutes)

```bash
# Start interactive mode
npm start
```

You should see:
```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              Odoo Agent - Node.js Edition                     ║
║         AI-Powered Odoo Development Assistant                 ║
║            Using Toon Format for Token Efficiency             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Current LLM Provider: gemini
Odoo Version: 16.0
Addons Path: ./addons

What would you like to do?
> 📦 Create a new Odoo module
  🔧 Customize an existing module
  🐛 Debug an Odoo issue
  🔍 Analyze code quality
  ⚙️  Settings
  ❌ Exit
```

## Step 4: Create Your First Module

Select "Create a new Odoo module" and follow the prompts:

```
Module name: hello_world
Description: My first Odoo module
Features: simple model, basic form view, menu item

[AI generates the module structure...]

Would you like to review the changes in detail? No

Apply 5 changes? Yes

✓ Created: ./addons/hello_world/__manifest__.py
✓ Created: ./addons/hello_world/__init__.py
✓ Created: ./addons/hello_world/models/__init__.py
✓ Created: ./addons/hello_world/models/hello.py
✓ Created: ./addons/hello_world/views/hello_views.xml

✨ Module created successfully!
```

## Step 5: Install in Odoo

```bash
# Copy module to your Odoo addons directory
cp -r ./addons/hello_world /path/to/your/odoo/addons/

# Restart Odoo
sudo systemctl restart odoo

# In Odoo web interface:
# 1. Enable Developer Mode
# 2. Apps menu → Update Apps List
# 3. Search for "hello_world"
# 4. Click Install
```

Done! 🎉

## Quick Command Reference

```bash
# Interactive mode
npm start

# Create module
node index.js create my_module \
  --description "Description" \
  --features "feature1, feature2"

# Customize module
node index.js customize ./addons/my_module \
  --request "Add custom field"

# Debug issue
node index.js debug \
  --error "Error message here"

# Analyze code
node index.js analyze ./addons/my_module/models/model.py

# Show config
node index.js config

# Switch provider
node index.js provider openai
```

## Common First-Time Issues

### "API_KEY is not configured"
→ Make sure you've edited `.env` and added your API key

### "Module not found at path"
→ Check that `ODOO_ADDONS_PATH` in `.env` points to a valid directory

### "Failed to parse AI response"
→ Network issue or token limit. Try again or check your internet connection

## Next Steps

- Read [README.md](README.md) for detailed documentation
- Check [EXAMPLES.md](EXAMPLES.md) for more usage examples
- Customize your `.env` settings for your environment
- Try creating more complex modules!

## Getting Help

1. Check [EXAMPLES.md](EXAMPLES.md) for similar use cases
2. Review error messages carefully
3. Try `node index.js config` to verify settings
4. Check that your API key is valid and has credits

## Pro Tips

1. **Start Simple**: Create basic modules first, then add complexity
2. **Review Changes**: Always review diffs before approving
3. **Use Backups**: The agent creates automatic backups (`.backup_*` files)
4. **Low Temperature**: Keep `LLM_TEMPERATURE=0.1` for consistent code
5. **Descriptive Features**: Be specific about what you want

---

Ready to build amazing Odoo modules? Run `npm start` and let's go! 🚀
