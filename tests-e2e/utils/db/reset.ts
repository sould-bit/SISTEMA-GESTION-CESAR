// 🧹 DB Reset & Seed Automation
// Recreates the test database and population via 'manage.py' commands.

import { dbPool, checkConnection } from './connection';
import { logger } from '../logger';
import path from 'path';
import { spawn } from 'child_process';

/**
 * 🧹 DB Reset & Seed Automation
 * Recreates the test database and population via 'manage.py' commands.
 * Resolves once the database is fully migrated and seeded.
 */
export const resetDatabase = async () => {
    logger.section('Reseteando Base de Datos Test (Docker)');

    const dockerCwd = path.resolve(__dirname, '../../');
    const projectRoot = path.resolve(__dirname, '../../../'); // manage.py is in root
    const TEST_DB_URL = `postgresql://cesar_test_user:cesar_test_password@127.0.0.1:5433/cesar_test_db`;

    const env = {
        ...process.env,
        DATABASE_URL: TEST_DB_URL,
        DB_PORT: '5433',
        DB_HOST: '127.0.0.1',
        DB_USER: 'cesar_test_user',
        DB_PASSWORD: 'cesar_test_password',
        DB_NAME: 'cesar_test_db',
        SECRET_KEY: process.env.SECRET_KEY || 'test_secret_key_123',
        ALGORITHM: 'HS256',
        PYTHONPATH: projectRoot,
        PYTHONIOENCODING: 'utf-8',
        BACKEND_CONTAINER: 'backend_FastOps_Test',
        DB_CONTAINER: 'cesar_test_db'
    };

    try {
        const runCommand = (cmd: string) => {
            return new Promise<void>((resolve, reject) => {
                const child = spawn(cmd, {
                    cwd: cmd.includes('docker') ? dockerCwd : projectRoot,
                    env,
                    shell: true
                });

                let output = '';
                child.stdout?.on('data', (data) => {
                    output += data.toString();
                    process.stdout.write(data);
                });
                child.stderr?.on('data', (data) => {
                    output += data.toString();
                    process.stderr.write(data);
                });

                child.on('close', (code: number | null) => {
                    if (code === 0) resolve();
                    else {
                        logger.error(`Command failed: ${cmd}\nOutput:\n${output}`, 'CMD');
                        reject(new Error(`Command ${cmd} failed with code ${code}`));
                    }
                });

                child.on('error', (err: Error) => {
                    reject(err);
                });
            });
        };

        // 0. Cleanup previous state (including volumes)
        logger.info('Cleaning up existing test environment...', 'DOCKER');
        await runCommand('docker-compose -f docker-compose.test.yml down -v');

        // 1. Docker Compose
        logger.info('Ensuring Docker container is running...', 'DOCKER');
        await runCommand('docker-compose -f docker-compose.test.yml up -d --build --force-recreate');

        // Give Docker 3 seconds to stabilize port mapping
        await new Promise(r => setTimeout(r, 3000));

        // Step 1: Health Check before migrations
        logger.info('Verifying database connectivity...', 'DB');
        let connected = false;
        for (let i = 0; i < 5; i++) {
            connected = await checkConnection();
            if (connected) break;
            logger.warn(`Database connection attempt ${i + 1} failed. Retrying...`, 'DB');
            await new Promise(r => setTimeout(r, 2000));
        }

        if (!connected) {
            throw new Error('Could not connect to test database after several attempts.');
        }

        // 1. Run migrations (Alembic)
        logger.info('Running Alembic Migrations...', 'DB');
        await runCommand('python manage.py db upgrade');
        logger.success('Schema Migrated Successfully', 'DB');

        // 2. Seed Data (Genesis Mode)
        logger.info('Seeding System Config (Genesis) via manage.py...', 'DB');
        await runCommand('python manage.py db seed --genesis');
        logger.success('System Config Seeded Successfully', 'DB');

        // 📝 CRITICAL COMPLIANCE: Close the connection pool to avoid socket leaks
        await dbPool.end();
        logger.info('Database connection pool closed safely.', 'DB');

        return true;

    } catch (error) {
        logger.error('Failed to reset/seed database', 'DB', error);
        // Important: Still try to close the pool on error
        try { await dbPool.end(); } catch (e) { /* ignore */ }
        throw error;
    }
};

if (require.main === module) {
    resetDatabase().catch(err => {
        console.error(err);
        process.exit(1);
    });
}
