import chalk from 'chalk';
import { OdooAgent } from '../agent/odoo-agent.js';
import { UIHelpers } from '../utils/ui-helpers.js';
import config from '../config/config.js';

/**
 * Interactive CLI - Menu-driven interface
 */
export class InteractiveCLI {
  constructor() {
    this.agent = new OdooAgent();
  }

  /**
   * Start interactive mode
   */
  async start() {
    UIHelpers.showBanner();

    console.log(chalk.gray(`Current LLM Provider: ${chalk.bold(this.agent.getProviderName())}`));
    console.log(chalk.gray(`Odoo Version: ${chalk.bold(config.odoo.version)}`));
    console.log(chalk.gray(`Addons Path: ${chalk.bold(config.odoo.addonsPath)}\n`));

    let running = true;

    while (running) {
      const choice = await UIHelpers.askChoice(
        '\nWhat would you like to do?',
        [
          { name: '📦 Create a new Odoo module', value: 'create' },
          { name: '🔧 Customize an existing module', value: 'customize' },
          { name: '🐛 Debug an Odoo issue', value: 'debug' },
          { name: '🔍 Analyze code quality', value: 'analyze' },
          { name: '⚙️  Settings', value: 'settings' },
          { name: '❌ Exit', value: 'exit' }
        ]
      );

      switch (choice) {
        case 'create':
          await this.handleCreateModule();
          break;
        case 'customize':
          await this.handleCustomizeModule();
          break;
        case 'debug':
          await this.handleDebugIssue();
          break;
        case 'analyze':
          await this.handleAnalyzeCode();
          break;
        case 'settings':
          await this.handleSettings();
          break;
        case 'exit':
          console.log(chalk.cyan('\n👋 Goodbye!\n'));
          running = false;
          break;
      }
    }
  }

  /**
   * Handle module creation
   */
  async handleCreateModule() {
    console.log(chalk.bold.cyan('\n📦 Create New Odoo Module\n'));

    const moduleName = await UIHelpers.askInput(
      'Module name (snake_case):',
      'my_custom_module'
    );

    const description = await UIHelpers.askInput(
      'Module description:',
      'Custom module for specific functionality'
    );

    const features = await UIHelpers.askInput(
      'Required features (comma-separated):',
      'custom models, views, security rules'
    );

    const confirm = await UIHelpers.askConfirm(
      `Create module "${moduleName}"?`,
      true
    );

    if (confirm) {
      const result = await this.agent.createModule(moduleName, description, features);

      if (result.success) {
        console.log(chalk.green.bold('\n✨ Module created successfully!\n'));
        console.log(chalk.white(`Module location: ${chalk.cyan(result.modulePath)}\n`));
        console.log(chalk.yellow('Next steps:'));
        console.log(chalk.white('  1. Restart your Odoo server'));
        console.log(chalk.white('  2. Update the apps list'));
        console.log(chalk.white(`  3. Install the "${moduleName}" module\n`));
      }
    } else {
      console.log(chalk.yellow('\nOperation cancelled\n'));
    }
  }

  /**
   * Handle module customization
   */
  async handleCustomizeModule() {
    console.log(chalk.bold.cyan('\n🔧 Customize Existing Module\n'));

    const modulePath = await UIHelpers.askInput(
      'Module path:',
      config.odoo.addonsPath + '/my_module'
    );

    const customizationRequest = await UIHelpers.askInput(
      'What customization do you need?',
      'Add a custom field to sales orders with validation'
    );

    const confirm = await UIHelpers.askConfirm(
      'Proceed with customization?',
      true
    );

    if (confirm) {
      const result = await this.agent.customizeModule(modulePath, customizationRequest);

      if (result.success) {
        console.log(chalk.green.bold('\n✨ Module customized successfully!\n'));
        console.log(chalk.yellow('Next steps:'));
        console.log(chalk.white('  1. Restart your Odoo server'));
        console.log(chalk.white('  2. Update the module'));
        console.log(chalk.white('  3. Test the new functionality\n'));
      }
    } else {
      console.log(chalk.yellow('\nOperation cancelled\n'));
    }
  }

  /**
   * Handle debugging
   */
  async handleDebugIssue() {
    console.log(chalk.bold.cyan('\n🐛 Debug Odoo Issue\n'));

    const errorMessage = await UIHelpers.askInput(
      'Error message:',
      'AttributeError: \'sale.order\' object has no attribute \'custom_field\''
    );

    const hasCodeContext = await UIHelpers.askConfirm(
      'Do you have code context to provide?',
      false
    );

    let codeContext = '';
    if (hasCodeContext) {
      console.log(chalk.gray('\nPaste your code (press Enter twice when done):\n'));
      codeContext = await this.getMultilineInput();
    }

    const hasModulePath = await UIHelpers.askConfirm(
      'Is this related to a specific module?',
      false
    );

    let modulePath = '';
    if (hasModulePath) {
      modulePath = await UIHelpers.askInput('Module path:');
    }

    const result = await this.agent.debugIssue(errorMessage, codeContext, modulePath);

    if (result.success) {
      console.log(chalk.green.bold('\n✅ Diagnosis complete!\n'));
    }
  }

  /**
   * Handle code analysis
   */
  async handleAnalyzeCode() {
    console.log(chalk.bold.cyan('\n🔍 Analyze Code Quality\n'));

    const filePath = await UIHelpers.askInput(
      'File path to analyze:',
      config.odoo.addonsPath + '/my_module/models/model.py'
    );

    const result = await this.agent.analyzeCode(filePath);

    if (result.success) {
      console.log(chalk.green.bold('\n✅ Analysis complete!\n'));
    }
  }

  /**
   * Handle settings
   */
  async handleSettings() {
    console.log(chalk.bold.cyan('\n⚙️  Settings\n'));

    const action = await UIHelpers.askChoice(
      'What would you like to configure?',
      [
        { name: '🤖 Change LLM Provider', value: 'provider' },
        { name: '📁 View Current Configuration', value: 'view' },
        { name: '🔙 Back', value: 'back' }
      ]
    );

    if (action === 'provider') {
      const currentProvider = this.agent.getProviderName();
      console.log(chalk.gray(`\nCurrent provider: ${chalk.bold(currentProvider)}\n`));

      const newProvider = await UIHelpers.askChoice(
        'Select new provider:',
        [
          { name: 'Gemini (Google)', value: 'gemini' },
          { name: 'OpenAI (GPT-4)', value: 'openai' },
          { name: 'Anthropic (Claude)', value: 'anthropic' }
        ]
      );

      if (newProvider !== currentProvider) {
        this.agent.switchProvider(newProvider);
      }
    } else if (action === 'view') {
      console.log(chalk.bold('\nCurrent Configuration:\n'));
      console.log(chalk.cyan('LLM Provider:'), config.llm.provider);
      console.log(chalk.cyan('Temperature:'), config.llm.temperature);
      console.log(chalk.cyan('Max Tokens:'), config.llm.maxTokens);
      console.log(chalk.cyan('Odoo Version:'), config.odoo.version);
      console.log(chalk.cyan('Addons Path:'), config.odoo.addonsPath);
      console.log(chalk.cyan('Auto Approve:'), config.agent.autoApprove);
      console.log(chalk.cyan('Backup Files:'), config.agent.backupFiles);
      console.log(chalk.cyan('Use Toon Format:'), config.agent.useToonFormat);
      console.log();
    }
  }

  /**
   * Get multiline input from user
   * @returns {Promise<string>}
   */
  async getMultilineInput() {
    return new Promise((resolve) => {
      const lines = [];
      let emptyLineCount = 0;

      process.stdin.on('data', (data) => {
        const line = data.toString().trim();

        if (line === '') {
          emptyLineCount++;
          if (emptyLineCount >= 2) {
            process.stdin.pause();
            resolve(lines.join('\n'));
          }
        } else {
          emptyLineCount = 0;
          lines.push(line);
        }
      });
    });
  }
}

export default InteractiveCLI;
