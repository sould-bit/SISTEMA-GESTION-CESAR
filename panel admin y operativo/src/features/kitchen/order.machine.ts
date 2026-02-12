import { createMachine, assign } from 'xstate';
import { Order, OrderStatus } from '../admin/types';
import { api } from '@/lib/api';

/**
 * Order State Machine - Aligned with Backend V4.1
 * Handles the lifecycle of a kitchen order with automatic API synchronization.
 */

export interface OrderContext {
    order: Order;
    error: string | null;
}

export type OrderEvent =
    | { type: 'CONFIRM' }
    | { type: 'PREPARE' }
    | { type: 'READY' }
    | { type: 'DELIVER' }
    | { type: 'CANCEL' }
    | { type: 'UPDATE_ORDER'; order: Order };

export const orderMachine = createMachine({
    id: 'order',
    types: {} as {
        context: OrderContext;
        events: OrderEvent;
        input: { order: Order };
    },
    initial: 'determining',
    context: ({ input }) => ({
        order: input.order,
        error: null,
    }),
    states: {
        determining: {
            always: [
                { target: 'cancelled', guard: ({ context }) => context.order.status === 'cancelled' },
                { target: 'delivered', guard: ({ context }) => context.order.status === 'delivered' },
                { target: 'ready', guard: ({ context }) => context.order.status === 'ready' },
                { target: 'preparing', guard: ({ context }) => context.order.status === 'preparing' },
                { target: 'confirmed', guard: ({ context }) => context.order.status === 'confirmed' },
                { target: 'pending', guard: ({ context }) => context.order.status === 'pending' },
            ],
        },
        pending: {
            on: {
                CONFIRM: 'updating'
            },
        },
        confirmed: {
            on: {
                PREPARE: 'updating'
            },
        },
        preparing: {
            on: {
                READY: 'updating'
            },
        },
        ready: {
            on: {
                DELIVER: 'updating'
            },
        },
        updating: {
            invoke: {
                src: 'updateStatus',
                input: ({ event }) => {
                    const nextStatusMap: Record<string, OrderStatus> = {
                        CONFIRM: 'confirmed',
                        PREPARE: 'preparing',
                        READY: 'ready',
                        DELIVER: 'delivered',
                        CANCEL: 'cancelled'
                    };
                    return { status: nextStatusMap[event.type] };
                },
                onDone: {
                    target: 'determining',
                    actions: assign({
                        order: ({ context, event }) => ({ ...context.order, status: event.output.status })
                    })
                },
                onError: {
                    target: 'determining',
                    actions: assign({
                        error: ({ event }) => (event.error as Error).message
                    })
                }
            }
        },
        delivered: { type: 'final' },
        cancelled: { type: 'final' },
    },
    on: {
        UPDATE_ORDER: {
            actions: assign({
                order: ({ event }) => event.order
            }),
            target: '.determining'
        }
    }
}, {
    actors: {
        updateStatus: async ({ input, context }: { input: { status: OrderStatus }, context: OrderContext }) => {
            const { data } = await api.patch(`/orders/${context.order.id}/status`, { status: input.status });
            return data;
        }
    }
});
