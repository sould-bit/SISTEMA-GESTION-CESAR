import { spawn, ChildProcess } from 'child_process';
import { logger } from '../logger';
import path from 'path';

let frontendProcess: ChildProcess | null = null;
const PORT = 5174;
const HEALTH_URL = `http://localhost:${PORT}/`; // Front is just HTML

export const startFrontend = async () => {
    logger.section('Levantando Frontend (Test Env)');

    return new Promise<void>((resolve, reject) => {
        const frontendPath = path.resolve(__dirname, '../../../panel admin y operativo');

        // Environment variables for TEST mode
        const env = {
            ...process.env,
            VITE_PORT: String(PORT),
            VITE_API_URL: 'http://127.0.0.1:8001', // Point to Test Backend explicit IP
            BROWSER: 'none', // Don't open browser automatically
            FORCE_COLOR: '1' // Keep colors in output
        };

        logger.info(`Starting Vite on port ${PORT}... (API: ${env.VITE_API_URL})`, 'FRONTEND');

        const cmd = `npm run dev -- --port ${PORT}`;
        frontendProcess = spawn(cmd, {
            cwd: frontendPath,
            env: env,
            shell: true
        });

        frontendProcess.stdout?.on('data', (data) => {
            const str = data.toString();
            if (str.includes(String(PORT))) {
                logger.success('Vite started on ' + PORT, 'FRONTEND');
            }
        });

        frontendProcess.stderr?.on('data', (data) => {
            const msg = data.toString();
            // Vite outputs harmless warnings to stderr sometimes, ignore unless error
            if (msg.toLowerCase().includes('error')) logger.warn(msg, 'FRONTEND');
        });

        frontendProcess.on('close', (code) => {
            if (code !== 0 && code !== null) {
                logger.error(`Frontend process exited with code ${code}`, 'FRONTEND');
                reject(new Error('Frontend crashed'));
            }
        });

        // Wait for port to be reachable
        // Simple polling mechanism
        const checkHealth = async (retries = 30) => {
            if (retries === 0) {
                stopFrontend();
                reject(new Error('Frontend timed out (Health check failed)'));
                return;
            }

            try {
                const resp = await fetch(HEALTH_URL);
                if (resp.status === 200) {
                    logger.success(`Frontend is READY at ${HEALTH_URL}`, 'FRONTEND');
                    resolve();
                } else {
                    throw new Error('Not 200');
                }
            } catch (e) {
                setTimeout(() => checkHealth(retries - 1), 1000);
            }
        };

        // Give it a second to start booting before polling
        setTimeout(() => checkHealth(), 1000);
    });
};

export const stopFrontend = () => {
    if (frontendProcess && frontendProcess.pid) {
        logger.info('Stopping Frontend...', 'FRONTEND');
        if (process.platform === 'win32') {
            spawn('taskkill', ['/F', '/T', '/PID', String(frontendProcess.pid)], { shell: true });
        } else {
            frontendProcess.kill();
        }
        frontendProcess = null;
    }
};
