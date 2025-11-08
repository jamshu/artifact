import { Command } from 'commander';
import chalk from 'chalk';
import { OdooAgent } from '../agent/odoo-agent.js';
import { UIHelpers } from '../utils/ui-helpers.js';
import config from '../config/config.js';

/**
 * Command-based CLI - Direct command execution
 */
export class CommandCLI {
  constructor() {
    this.program = new Command();
    this.agent = new OdooAgent();
    this.setupCommands();
  }

  /**
   * Setup command definitions
   */
  setupCommands() {
    this.program
      .name('odoo-agent')
      .description('AI-powered Odoo development assistant using Toon format')
      .version('1.0.0');

    // Create module command
    this.program
      .command('create <module-name>')
      .description('Create a new Odoo module')
      .option('-d, --description <text>', 'Module description')
      .option('-f, --features <text>', 'Required features (comma-separated)')
      .option('-y, --yes', 'Auto-approve changes', false)
      .action(async (moduleName, options) => {
        await this.handleCreateCommand(moduleName, options);
      });

    // Customize module command
    this.program
      .command('customize <module-path>')
      .description('Customize an existing Odoo module')
      .option('-r, --request <text>', 'Customization request')
      .option('-y, --yes', 'Auto-approve changes', false)
      .action(async (modulePath, options) => {
        await this.handleCustomizeCommand(modulePath, options);
      });

    // Debug command
    this.program
      .command('debug')
      .description('Debug an Odoo issue')
      .option('-e, --error <message>', 'Error message')
      .option('-c, --context <code>', 'Code context')
      .option('-m, --module <path>', 'Module path')
      .option('-y, --yes', 'Auto-approve fixes', false)
      .action(async (options) => {
        await this.handleDebugCommand(options);
      });

    // Analyze command
    this.program
      .command('analyze <file-path>')
      .description('Analyze code quality')
      .action(async (filePath) => {
        await this.handleAnalyzeCommand(filePath);
      });

    // Interactive mode command
    this.program
      .command('interactive')
      .alias('i')
      .description('Start interactive mode')
      .action(async () => {
        const { InteractiveCLI } = await import('./interactive.js');
        const interactive = new InteractiveCLI();
        await interactive.start();
      });

    // Config command
    this.program
      .command('config')
      .description('Show current configuration')
      .action(() => {
        this.showConfig();
      });

    // Provider command
    this.program
      .command('provider <name>')
      .description('Switch LLM provider (gemini, openai, anthropic)')
      .action((name) => {
        this.switchProvider(name);
      });
  }

  /**
   * Handle create module command
   */
  async handleCreateCommand(moduleName, options) {
    try {
      const description = options.description || await UIHelpers.askInput(
        'Module description:',
        'Custom module'
      );

      const features = options.features || await UIHelpers.askInput(
        'Required features:',
        'models, views, security'
      );

      if (options.yes) {
        config.agent.autoApprove = true;
      }

      const result = await this.agent.createModule(moduleName, description, features);

      if (result.success) {
        UIHelpers.showSuccess('Module created successfully!');
        console.log(chalk.white(`Location: ${chalk.cyan(result.modulePath)}\n`));
        process.exit(0);
      } else {
        UIHelpers.showError(result.message || 'Failed to create module');
        process.exit(1);
      }
    } catch (error) {
      UIHelpers.showError(error.message);
      process.exit(1);
    }
  }

  /**
   * Handle customize module command
   */
  async handleCustomizeCommand(modulePath, options) {
    try {
      const request = options.request || await UIHelpers.askInput(
        'Customization request:',
        'Add custom functionality'
      );

      if (options.yes) {
        config.agent.autoApprove = true;
      }

      const result = await this.agent.customizeModule(modulePath, request);

      if (result.success) {
        UIHelpers.showSuccess('Module customized successfully!');
        process.exit(0);
      } else {
        UIHelpers.showError(result.message || 'Failed to customize module');
        process.exit(1);
      }
    } catch (error) {
      UIHelpers.showError(error.message);
      process.exit(1);
    }
  }

  /**
   * Handle debug command
   */
  async handleDebugCommand(options) {
    try {
      const errorMessage = options.error || await UIHelpers.askInput(
        'Error message:'
      );

      const codeContext = options.context || '';
      const modulePath = options.module || '';

      if (options.yes) {
        config.agent.autoApprove = true;
      }

      const result = await this.agent.debugIssue(errorMessage, codeContext, modulePath);

      if (result.success) {
        UIHelpers.showSuccess('Diagnosis complete!');
        process.exit(0);
      } else {
        UIHelpers.showError(result.message || 'Debug failed');
        process.exit(1);
      }
    } catch (error) {
      UIHelpers.showError(error.message);
      process.exit(1);
    }
  }

  /**
   * Handle analyze command
   */
  async handleAnalyzeCommand(filePath) {
    try {
      const result = await this.agent.analyzeCode(filePath);

      if (result.success) {
        UIHelpers.showSuccess('Analysis complete!');
        process.exit(0);
      } else {
        UIHelpers.showError(result.message || 'Analysis failed');
        process.exit(1);
      }
    } catch (error) {
      UIHelpers.showError(error.message);
      process.exit(1);
    }
  }

  /**
   * Show configuration
   */
  showConfig() {
    console.log(chalk.bold.cyan('\n⚙️  Configuration:\n'));
    console.log(chalk.cyan('LLM Provider:'), chalk.white(config.llm.provider));
    console.log(chalk.cyan('Temperature:'), chalk.white(config.llm.temperature));
    console.log(chalk.cyan('Max Tokens:'), chalk.white(config.llm.maxTokens));
    console.log(chalk.cyan('Odoo Version:'), chalk.white(config.odoo.version));
    console.log(chalk.cyan('Addons Path:'), chalk.white(config.odoo.addonsPath));
    console.log(chalk.cyan('Auto Approve:'), chalk.white(config.agent.autoApprove));
    console.log(chalk.cyan('Backup Files:'), chalk.white(config.agent.backupFiles));
    console.log(chalk.cyan('Use Toon Format:'), chalk.white(config.agent.useToonFormat));
    console.log();
  }

  /**
   * Switch LLM provider
   */
  switchProvider(name) {
    try {
      this.agent.switchProvider(name);
      console.log(chalk.green(`\n✓ Switched to ${name} provider\n`));
    } catch (error) {
      UIHelpers.showError(error.message);
      process.exit(1);
    }
  }

  /**
   * Run the CLI
   */
  async run() {
    await this.program.parseAsync(process.argv);
  }
}

export default CommandCLI;
