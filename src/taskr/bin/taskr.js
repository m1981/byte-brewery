#!/usr/bin/env node
const { version } = require('../package.json');
console.log(`Taskr v${version}`);

const inquirer = require('inquirer');
const chalk = require('chalk');
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

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

function buildChoices() {
  return [
    ...favorites.length > 0 ? [new inquirer.Separator(chalk.yellow('★ FAVORITES ★'))] : [],
        ...favorites.map(name => ({
      name: `${chalk.yellow('★')} ${chalk.green(name)}: ${chalk.dim(scripts[name])}`,
            value: name
        })),
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
      name: chalk.red('✖ Exit'),
      value: 'EXIT'
        }
    ];
}

let choices = buildChoices();

// Function to run the main menu
function showMainMenu() {
    inquirer.prompt([
        {
            type: 'list',
            name: 'scriptName',
            message: 'Select a script to run:',
            choices,
            pageSize: 15
        }
    ])
        .then(answers => {
            if (answers.scriptName === 'MANAGE_FAVORITES') {
                showFavoritesMenu();
                return;
            }

            const command = `pnpm run ${answers.scriptName}`;
            console.log(`\nExecuting: ${command}\n`);

            try {
                execSync(command, { stdio: 'inherit', cwd: path.dirname(packageJsonPath) });
            } catch (error) {
                console.error('Script execution failed');
            }

            // Return to the menu after script execution
            console.log('\nReturning to script menu...\n');
            showMainMenu();
        })
        .catch(error => {
            console.error('An error occurred:', error.message);
            process.exit(1);
        });
}

// Function to manage favorites
function showFavoritesMenu() {
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

// Start the application
showMainMenu();

