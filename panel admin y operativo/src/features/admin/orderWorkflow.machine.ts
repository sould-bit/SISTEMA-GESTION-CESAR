import { createMachine, assign, fromPromise } from 'xstate';
import { api } from '../../lib/api';

export interface OrderWorkflowContext {
    orderId: number;
    currentStatus: string;
    permissions: string[];
    error: string | null;
    nextStatus?: string;
}

export type OrderWorkflowEvent =
    | { type: 'ACCEPT' }
    | { type: 'MARK_READY' }
    | { type: 'DELIVER' }
    | { type: 'CANCEL'; reason: string }
    | { type: 'REQUEST_CANCELLATION'; reason: string }
    | { type: 'REJECT_CANCELLATION' }
    | { type: 'APPROVE_CANCELLATION' };

export const orderWorkflowMachine = createMachine({
    id: 'orderWorkflow',
    types: {} as {
        context: OrderWorkflowContext;
        events: OrderWorkflowEvent;
        input: { orderId: number; status: string; permissions: string[] };
    },
    context: ({ input }) => ({
        orderId: input.orderId,
        currentStatus: input.status,
        permissions: input.permissions,
        error: null,
    }),
    initial: 'idle',
    states: {
        idle: {
            always: [
                { target: 'pending', guard: ({ context }) => context.currentStatus === 'pending' },
                { target: 'preparing', guard: ({ context }) => context.currentStatus === 'preparing' },
                { target: 'ready', guard: ({ context }) => context.currentStatus === 'ready' },
                { target: 'delivered', guard: ({ context }) => context.currentStatus === 'delivered' },
                { target: 'cancelled', guard: ({ context }) => context.currentStatus === 'cancelled' },
            ]
        },
        pending: {
            on: {
                ACCEPT: {
                    target: 'updating',
                    guard: 'canUpdate',
                    actions: assign({ nextStatus: () => 'preparing' })
                },
                CANCEL: {
                    target: 'updating',
                    guard: 'canCancelDirectly',
                    actions: assign({ nextStatus: () => 'cancelled' })
                }
            }
        },
        preparing: {
            on: {
                MARK_READY: {
                    target: 'updating',
                    guard: 'canUpdate',
                    actions: assign({ nextStatus: () => 'ready' })
                }
            }
        },
        ready: {
            on: {
                DELIVER: {
                    target: 'updating',
                    guard: 'canUpdate',
                    actions: assign({ nextStatus: () => 'delivered' })
                }
            }
        },
        updating: {
            invoke: {
                src: 'updateStatus',
                input: ({ context }) => ({
                    orderId: context.orderId,
                    status: (context as any).nextStatus
                }),
                onDone: {
                    target: 'idle',
                    actions: assign({
                        currentStatus: ({ event }) => event.output.status,
                        error: () => null
                    })
                },
                onError: {
                    target: 'idle',
                    actions: assign({ error: ({ event }) => (event.error as Error).message })
                }
            }
        },
        delivered: { type: 'final' },
        cancelled: { type: 'final' }
    }
}, {
    guards: {
        canUpdate: ({ context }) => context.permissions.includes('orders.update'),
        canCancelDirectly: ({ context }) => context.permissions.includes('orders.cancel'),
        canManageAll: ({ context }) => context.permissions.includes('orders.manage_all'),
    },
    actors: {
        updateStatus: fromPromise(async ({ input }: { input: { orderId: number; status: string } }) => {
            const response = await api.patch(`/orders/${input.orderId}/status`, { status: input.status });
            return response.data;
        })
    }
});
