import { spawn, ChildProcess } from 'child_process';
import { logger } from '../logger';
import path from 'path';

let backendProcess: ChildProcess | null = null;
const PORT = 8001;
const HEALTH_URL = `http://127.0.0.1:${PORT}/docs`; // Docs is a good health check

export const startBackend = async () => {
    logger.section('Verificando Backend (Docker Test Env)');

    return new Promise<void>((resolve, reject) => {
        const checkHealth = async (retries = 30) => {
            if (retries === 0) {
                reject(new Error('Backend timed out (Health check failed - Docker container not reachable)'));
                return;
            }

            try {
                // Determine fetch availability (Node 18+)
                const resp = await fetch(HEALTH_URL);
                if (resp.status === 200) {
                    logger.success(`Backend is READY at ${HEALTH_URL}`, 'BACKEND');
                    resolve();
                } else {
                    throw new Error('Not 200');
                }
            } catch (e) {
                logger.info(`Waiting for backend... (${retries} retries left)`, 'BACKEND');
                setTimeout(() => checkHealth(retries - 1), 1000);
            }
        };

        // Start polling immediatelly
        checkHealth();
    });
};

export const stopBackend = () => {
    if (backendProcess && backendProcess.pid) {
        logger.info('Stopping Backend...', 'BACKEND');
        if (process.platform === 'win32') {
            // Kill the entire process tree on Windows
            spawn('taskkill', ['/F', '/T', '/PID', String(backendProcess.pid)], { shell: true });
        } else {
            backendProcess.kill();
        }
        backendProcess = null;
    }
};
