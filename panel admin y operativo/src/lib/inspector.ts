import { createBrowserInspector } from '@statelyai/inspect';

// Initialize Stately Inspector for visual debugging in development
export const inspector = typeof window !== 'undefined' && import.meta.env.DEV
    ? createBrowserInspector({
        autoStart: true,
    })
    : undefined;
