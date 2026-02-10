// 📝 Centralized Logging Utility for E2E Tests
// Ensures 100% traceability of setup/teardown steps.

const COLORS = {
    blue: '\x1b[34m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    red: '\x1b[31m',
    reset: '\x1b[0m',
    dim: '\x1b[2m'
};

const timestamp = () => new Date().toISOString().split('T')[1].split('.')[0];

export const logger = {
    info: (msg: string, context: string = 'E2E') => {
        console.log(`${COLORS.dim}[${timestamp()}]${COLORS.reset} ${COLORS.blue}[${context.toUpperCase()}]${COLORS.reset} ${msg}`);
    },

    success: (msg: string, context: string = 'E2E') => {
        console.log(`${COLORS.dim}[${timestamp()}]${COLORS.reset} ${COLORS.green}[${context.toUpperCase()}]${COLORS.reset} ✔ ${msg}`);
    },

    warn: (msg: string, context: string = 'E2E') => {
        console.log(`${COLORS.dim}[${timestamp()}]${COLORS.reset} ${COLORS.yellow}[${context.toUpperCase()}]${COLORS.reset} ⚠️  ${msg}`);
    },

    error: (msg: string, context: string = 'E2E', err?: any) => {
        console.error(`${COLORS.dim}[${timestamp()}]${COLORS.reset} ${COLORS.red}[${context.toUpperCase()}]${COLORS.reset} ❌ ${msg}`);
        if (err) console.error(err);
    },

    section: (title: string) => {
        console.log(`\n${COLORS.blue}➤ ${title.toUpperCase()}${COLORS.reset}`);
        console.log(`${COLORS.dim}────────────────────────────────────────${COLORS.reset}`);
    }
};
