#!/usr/bin/env tsx
import * as ts from 'typescript';
import * as fs from 'fs';

/**
 * Parses TypeScript code and removes function/method/arrow bodies.
 */
function generateTsSummary(sourceCode: string): string {
    const sourceFile = ts.createSourceFile(
        'module.ts',
        sourceCode,
        ts.ScriptTarget.Latest,
        true
    );

    const bodiesToRemove: { start: number; end: number }[] = [];

    function visit(node: ts.Node) {
        // 1. Standard Functions & Methods
        if ((ts.isFunctionDeclaration(node) || ts.isMethodDeclaration(node)) && node.body) {
            bodiesToRemove.push({
                start: node.body.getStart(sourceFile),
                end: node.body.getEnd()
            });
        }
        // 2. Arrow Functions (used heavily in SvelteKit load/actions)
        else if (ts.isArrowFunction(node)) {
            // If the arrow function has a block body { ... }
            if (ts.isBlock(node.body)) {
                bodiesToRemove.push({
                    start: node.body.getStart(sourceFile),
                    end: node.body.getEnd()
                });
            } else {
                // If it's an implicit return arrow function: () => something
                bodiesToRemove.push({
                    start: node.equalsGreaterThanToken.getEnd(),
                    end: node.body.getEnd()
                });
            }
        }

        ts.forEachChild(node, visit);
    }

    visit(sourceFile);
    // 1. Sort ascending by start position
    bodiesToRemove.sort((a, b) => a.start - b.start);

    // 2. Filter out nested bodies (e.g., arrow functions inside standard functions)
    const outermostBodies: { start: number; end: number }[] = [];
    let currentOuter: { start: number; end: number } | null = null;

    for (const body of bodiesToRemove) {
        if (!currentOuter) {
            currentOuter = body;
        } else if (body.start >= currentOuter.start && body.end <= currentOuter.end) {
            // This body is inside the current outer body, ignore it
            continue;
        } else {
            outermostBodies.push(currentOuter);
            currentOuter = body;
        }
    }
    if (currentOuter) outermostBodies.push(currentOuter);

    // 3. Sort descending so slicing doesn't shift indices
    outermostBodies.sort((a, b) => b.start - a.start);

    let result = sourceCode;
    for (const { start, end } of outermostBodies) {
        result = result.slice(0, start) + result.slice(end);
    }

    return result.split('\n').map(line => line.trimEnd()).join('\n');
}

/**
 * Extracts the <script> tag from a .svelte file and summarizes it.
 */
function processSvelteFile(sourceCode: string): string {
    // Match <script ...> ... </script>
    const scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
    let match;
    let summary = '';

    while ((match = scriptRegex.exec(sourceCode)) !== null) {
        const scriptContent = match[1];
        summary += generateTsSummary(scriptContent) + '\n';
    }

    return summary.trim() || '// No script tag found or only HTML template present.';
}

// --- CLI Argument Parsing ---
const args = process.argv.slice(2);
const files: string[] = [];
let outputFile: string | null = null;

for (let i = 0; i < args.length; i++) {
    if (args[i] === '-o' || args[i] === '--output') {
        outputFile = args[i + 1];
        i++; // Skip the next argument since it's the filename
    } else {
        files.push(args[i]);
    }
}

if (files.length === 0) {
    console.error("No files provided.");
    process.exit(1);
}

// --- Processing ---
let outputContent = '';

for (const file of files) {
    if (!fs.existsSync(file)) {
        console.warn(`Warning: File not found: ${file}`);
        continue;
    }

    const code = fs.readFileSync(file, 'utf-8');
    let summary = '';

    if (file.endsWith('.svelte')) {
        summary = processSvelteFile(code);
    } else if (file.endsWith('.ts') || file.endsWith('.js')) {
        summary = generateTsSummary(code);
    } else {
        continue; // Skip unknown file types
    }

    outputContent += `${file}\n\`\`\`typescript\n${summary.trim()}\n\`\`\`\n\n`;
}

// --- Output ---
if (outputFile) {
    fs.writeFileSync(outputFile, outputContent, 'utf-8');
    console.log(`Successfully wrote summary for ${files.length} files to ${outputFile}`);
} else {
    process.stdout.write(outputContent);
}