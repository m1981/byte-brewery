#!/usr/bin/env node
const { version } = require('../package.json');
console.log(`Taskr v${version}`);

const inquirer = require('inquirer');
const chalk = require('chalk');
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Get the directory where the script is located
const scriptDir = __dirname;

// Read package.json from the same directory as the script
const packageJsonPath = path.join(scriptDir, 'package.json');
let packageJson = {};
let scripts = {};

try {
    // Get the current working directory
    const currentDir = process.cwd();
    const packageJsonPath = path.join(currentDir, 'package.json');

    if (fs.existsSync(packageJsonPath)) {
        packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
        scripts = packageJson.scripts || {};
        console.log(`Found package.json in ${currentDir}`);
    } else {
        console.error('Error: Could not find package.json in the current directory.');
        console.log('Please run this script from a directory containing a package.json file.');
            process.exit(1);
        }
} catch (error) {
    console.error(`Error reading package.json: ${error.message}`);
    process.exit(1);
}

// Path to favorites file
const favoritesPath = path.join(process.cwd(), '.favorites');

// Read favorites file if it exists
let favorites = [];
try {
    if (fs.existsSync(favoritesPath)) {
        favorites = fs.readFileSync(favoritesPath, 'utf8')
            .split('\n')
            .filter(line => line.trim() && scripts[line.trim()]);
    }
} catch (error) {
    console.warn('Could not read favorites file:', error.message);
}

// Get all script names
const scriptNames = Object.keys(scripts);

if (scriptNames.length === 0) {
    console.log('No scripts found in package.json');
    process.exit(0);
}

// Set up keyboard input once at the start
    readline.emitKeypressEvents(process.stdin);
    if (process.stdin.isTTY) {
        process.stdin.setRawMode(true);
    }

// Increase max listeners to avoid warnings
process.stdin.setMaxListeners(20);

// Global variable to track the current prompt UI
let currentPromptUI = null;
let keypressHandlerActive = false;

function buildChoices() {
    const favoriteChoices = favorites.map((name, index) => ({
        name: `${chalk.yellow(index < 9 ? `[${index + 1}]` : '★')} ${chalk.green(name)}: ${chalk.dim(scripts[name])}`,
        value: name
    }));

  return [
    ...favorites.length > 0 ? [new inquirer.Separator(chalk.yellow('★ FAVORITES ★'))] : [],
        ...favoriteChoices,
    ...favorites.length > 0 ? [new inquirer.Separator(chalk.blue('ALL SCRIPTS'))] : [],
        ...scriptNames
            .filter(name => !favorites.includes(name))
            .map(name => ({
        name: `${chalk.green(name)}: ${chalk.dim(scripts[name])}`,
                value: name
            })),
        new inquirer.Separator(),
        {
      name: chalk.magenta('✎ Manage favorites...'),
            value: 'MANAGE_FAVORITES'
    },
    {
            name: chalk.red('✖ Exit [q]'),
      value: 'EXIT'
        }
    ];
}

let choices = buildChoices();

// Global keypress handler
function setupKeypressHandler() {
    if (keypressHandlerActive) return;

    keypressHandlerActive = true;

    // Set up the global keypress handler
    process.stdin.on('keypress', handleKeypress);
}

function removeKeypressHandler() {
    if (!keypressHandlerActive) return;

    process.stdin.removeListener('keypress', handleKeypress);
    keypressHandlerActive = false;
}

function handleKeypress(str, key) {
    // Only process keypresses when we have an active prompt
    if (!currentPromptUI) return;

    // 'q' to exit
    if (key.name === 'q') {
        currentPromptUI.close();
        process.exit(0);
    }

    // Number keys for favorites
    const num = parseInt(str);
    if (!isNaN(num) && num >= 1 && num <= 9 && num <= favorites.length) {
        currentPromptUI.close();
        currentPromptUI = null;
        runScript(favorites[num - 1]);
    }
}

// Function to run a script
function runScript(scriptName) {
    if (scriptName === 'EXIT') {
        process.exit(0);
        }

    if (scriptName === 'MANAGE_FAVORITES') {
                showFavoritesMenu();
                return;
            }

    // Get the current working directory where package.json is located
    const currentDir = process.cwd();

    // Use npm-run-path to ensure the correct environment
    const command = `npm run ${scriptName}`;
            console.log(`\nExecuting: ${command}\n`);

            try {
        // Temporarily disable raw mode while running the script
        if (process.stdin.isTTY) {
            process.stdin.setRawMode(false);
        }

        // Execute the command in the current directory
        execSync(command, {
            stdio: 'inherit',
            cwd: currentDir,
            env: { ...process.env, FORCE_COLOR: true }
        });
            } catch (error) {
                console.error('Script execution failed\n');
    } finally {
        // Re-enable raw mode after script completes
        if (process.stdin.isTTY) {
            process.stdin.setRawMode(true);
        }
            }
            showMainMenu();
}

// Function to run the main menu
function showMainMenu() {
    // Make sure keypress handler is set up
    setupKeypressHandler();

    const prompt = inquirer.prompt([
        {
            type: 'list',
            name: 'scriptName',
            message: 'Select a script to run:',
            choices,
            pageSize: 15
        }
    ]);

    // Store reference to the current prompt UI
    currentPromptUI = prompt.ui;

    prompt.then(answers => {
        currentPromptUI = null;
        runScript(answers.scriptName);
    }).catch(error => {
            console.error('An error occurred:', error.message);
            process.exit(1);
        });
}

// Function to manage favorites
function showFavoritesMenu() {
    // We don't need keypress shortcuts in the favorites menu
    removeKeypressHandler();

    const allScripts = Object.keys(scripts);

    inquirer
        .prompt([
            {
                type: 'checkbox',
                name: 'selectedFavorites',
                message: 'Select your favorite scripts:',
                choices: allScripts.map(name => ({
                    name: `${name}: ${scripts[name]}`,
                    value: name,
                    checked: favorites.includes(name)
                })),
                pageSize: 15
            }
        ])
        .then(answers => {
            // Update favorites
            favorites = answers.selectedFavorites;

            // Save to file
            try {
                fs.writeFileSync(favoritesPath, favorites.join('\n'));

                console.log('\nFavorites updated successfully!\n');
            } catch (error) {
                console.error(`Error saving favorites: ${error.message}`);
            }

            // Rebuild choices with new favorites
            choices = buildChoices();

            // Return to main menu
            showMainMenu();
        })
        .catch(error => {
            console.error('An error occurred:', error.message);
            showMainMenu(); // Return to main menu even if there's an error
        });
}

// Clean up on exit
process.on('exit', () => {
    if (process.stdin.isTTY) {
        process.stdin.setRawMode(false);
    }
    removeKeypressHandler();
});

// Handle Ctrl+C
process.on('SIGINT', () => {
    process.exit(0);
});

// Start the application
showMainMenu();

