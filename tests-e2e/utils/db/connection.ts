// 🔌 Modular DB Connection
// Connection Pooling for test database resets

import { Pool, Client } from 'pg';
import path from 'path';
import dotenv from 'dotenv';
import { logger } from '../logger';

// Load .env explicitly to ensure separation from root
dotenv.config({ path: path.resolve(__dirname, '../../.env') });

const config = {
    host: process.env.DB_HOST || '127.0.0.1',
    port: parseInt(process.env.DB_PORT || '5433'), // 5433 IS CRITICAL (Test DB)
    user: process.env.DB_USER || 'cesar_test_user',
    password: process.env.DB_PASSWORD || 'cesar_test_password',
    database: process.env.DB_NAME || 'cesar_test_db',
};

// Quick verification that we are NOT targeting PROD/DEV ports
if (config.port === 5432) {
    logger.error('CRITICAL: Attempting to run tests against PORT 5432 (PROD/DEV). Aborting.', 'DB');
    process.exit(1);
}

export const dbPool = new Pool(config);

export const checkConnection = async (): Promise<boolean> => {
    try {
        const client = await dbPool.connect();
        logger.info(`Connected to PostgreSQL: ${config.database}@${config.host}:${config.port}`, 'DB');
        client.release();
        return true;
    } catch (err) {
        logger.error('Failed to connect to Test Database', 'DB', err);
        return false;
    }
};
