// 🎬 E2E Runner (Orchestrator)
// Execute w// tests-e2e/start-e2e.ts

import { spawn } from 'child_process';
import path from 'path';
import dotenv from 'dotenv';
import { logger } from './utils/logger';

// 1. Load Enviroment Variables
const envPath = path.resolve(__dirname, '.env');
dotenv.config({ path: envPath });

const runTests = async () => {
    logger.section('🚀 INICIANDO TESTS E2E (LIVE ENVIRONMENT)');
    logger.info('⚠️  Using existing backend (8000) and frontend (5173). NO DATA RESET.', 'SETUP');

    try {
        // Run Playwright
        logger.section('🎭 EJECUTANDO PLAYWRIGHT');

        // Pass arguments to Playwright (e.g. file names)
        const args = process.argv.slice(2);
        const playwright = spawn('npx', ['playwright', 'test', ...args], {
            cwd: __dirname,
            stdio: 'inherit',
            shell: true,
            env: { ...process.env, CI: 'true' }
        });

        await new Promise<void>((resolve, reject) => {
            playwright.on('close', (code) => {
                if (code === 0) {
                    logger.success('✅ Tests Passed', 'PLAYWRIGHT');
                    resolve();
                } else {
                    logger.error(`❌ Tests Failed with code ${code}`, 'PLAYWRIGHT');
                    reject(new Error('Tests failed'));
                }
            });
        });

    } catch (error) {
        logger.error('Tests execution failed', 'MAIN');
        process.exit(1);
    }
};


// --- EXECUTE ---
runTests();
