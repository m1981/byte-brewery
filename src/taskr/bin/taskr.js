#!/usr/bin/env node

console.log('Taskr is starting...');
try {
    require('../src/index.js');
} catch (error) {
    console.error('Error loading taskr:', error);
}
