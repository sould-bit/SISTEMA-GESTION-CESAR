import { createMachine, assign, fromPromise, setup } from 'xstate';
import { tablesService, Table } from './tables.service';
import { api } from '../../lib/api';
import { Order } from '../admin/types';

export interface TablesContext {
    tables: Table[];
    tableOrders: Record<number, any>;
    activeTab: 'tables' | 'takeaway' | 'delivery';
    error: string | null;
    selectedOrder: Order | null;
    branchId: number | null;
}

export type TablesEvent =
    | { type: 'FETCH' }
    | { type: 'SET_TAB'; tab: 'tables' | 'takeaway' | 'delivery' }
    | { type: 'SELECT_TABLE'; table: Table; tableOrders: Record<number, any> }
    | { type: 'SETUP_TABLES'; count: number }
    | { type: 'REFRESH_ORDERS'; tableOrders: Record<number, any> }
    | { type: 'ORDER_FETCHED'; order: Order }
    | { type: 'CLOSE_DETAILS' };

export const tablesMachine = setup({
    types: {
        context: {} as TablesContext,
        events: {} as TablesEvent,
    },
    actors: {
        loadTables: fromPromise(async () => {
            return await tablesService.getTables();
        }),
        fetchOrder: fromPromise(async ({ input }: { input: { table: Table, tableOrders: any } }) => {
            const orderId = input.tableOrders[input.table.id]?.orderId;
            const path = orderId ? `/orders/${orderId}` : `/orders/active/table/${input.table.id}`;
            const res = await api.get<Order>(path);
            return res.data;
        }),
        setupTables: fromPromise(async ({ input }: { input: number }) => {
            await tablesService.setupTables(input);
            return await tablesService.getTables();
        })
    },
    actions: {
        notifyError: ({ event }) => console.error("Error:", event)
    }
}).createMachine({
    /** @xstate-layout N4IgpgJg5mDOIC5QBcCGAjANnAdJg9qhAJYB2UAxBPqWDmQG74DWdaWuBRZUCj+AY1TJiNANoAGALqSpiUAAd8sYiJryQAD0QBWABwA2HAEYDAJgAsei-oCcZgMwB2HQBoQAT0QPbOnOb0dCQkDB30HYz0AXyj3dmxYPEIScgowACd0-HScBUxhADNsgFsceM5knj5SJiE1UllZDSUVeo1tBH0jU0trO0cXdy8EJzNbHCcnQOCdHQczMwkzGLiMBPoIbAoAMQBRABUAYQAJJqQQFtVRUnbEUYccBYtbJwNjfUj5ocQrcYkp346YxOZwGAwrEDlRLETZgCgAZQOAH19gBBABCZ0Uyiu6nOHUMThwDmetgMr2czjcnkQwKJTlJOlsElmVgcegcEKhGy2iIAMrtDvsURiBViLji2vjdIYTOYrDY9PYqd8EMZgsTjJFLEsHMFjPYuWtcDDebsBUKReixcY5OdLlLQB11SScErbL4OQ4DLY9GY9KrjM8cKTbMY9f8tZEjRxobCEQcAKoABStAvh4od11uaokrvdnoc3t9-tVYzM-lJxnLNn1MfWprhACVdtsW-DjkiAPJNgAiuybGekzUl2elCC9bssLwkFmCSpJqr0xkeHpeBisZhBvic9dwBTAyAEAAseF30hAMlQaHR+KwysbEgej6fyOfL+lqrVhNdGsP7aOeJOogiwPHoegMhB4YcvYZiBuqExzDoiwcnoIT+joe5PoeJ5nheV4ZFkOR5IUJQPrGODPrhb74Z+-B1L+0iZoBNzjl0cq9IqyqDDSapBDgEhahyQT6H0FjgrEkKPjgDDEGAADueEfhQhx8l2iJIv2aIAJJ8kOdrYq0Y7AQgiwVhBpIWOyFjicYZZAjgzJhBItgkrYNgvBYWEyXJik0cpexHKc-6GbirEmWZboMh6VnWLZqqjBYAmhM8fpvBB-reekkDENlAgiOQ+z4AAcgp75XsxRlAVotJmAh5LPAYgmuf6hiBksEwekqOhgpY5KhN5sCHgVUCJgo160PQNQsGw0lDcgI1jV+gg-uITEhRKVXhTVarVuMG4eqJ1hTKWvEGuM532HOFhjLMW6DcNPBjWkmTZLk+TIEU6SlNy82LQoy0MWtMgbVm1XOkCSVkpYc5BI4yEWGWaETGCPX3GSBg6CC3mEdkOwHCclVhTm7zIz1lhFmhWrstSwxNeMN3WL4ebIb6XkQqQ+CXvA5xQiOW05gAtAYqqC34a4S5LHqcpJ3JcCkUD88T47OBIIZrnFEgcqYdm8U4GoUkC1gLE4vreY2SuOjtUE4OT4n2D11aI7xW4XWuFg9H6mWy9JVGvlA5XpJbxk7d6ej+NF7kfBEWPteM8yBGM9ifFB3myQpSkZMH4M-HBevho84HiXVmNLL4WU5XlI1FaV8mB9n23OnqK5O8zjjWWYItnTZAmmDom7BKbkwy6sFF-U9CgNyTepQ-3Qlki5rm68MZizI5qNsosBiBLMOOvUHAEC+Opiyj0jOztZSqqvTtsYe8s5Wc8xgxDEQA */
    id: 'tables',
    initial: 'loading',
    context: {
        tables: [],
        tableOrders: {},
        activeTab: 'tables',
        error: null,
        selectedOrder: null,
        branchId: null,
    },
    states: {
        loading: {
            invoke: {
                src: 'loadTables',
                onDone: {
                    target: 'idle',
                    actions: assign(({ event }) => ({
                        tables: event.output,
                        branchId: event.output.length > 0 ? event.output[0].branch_id : null
                    }))
                },
                onError: {
                    target: 'error',
                    actions: assign({
                        error: ({ event }) => (event.error as any)?.message || 'Error al cargar mesas'
                    })
                }
            }
        },
        idle: {
            on: {
                FETCH: 'loading',
                SET_TAB: {
                    actions: assign({ activeTab: ({ event }) => event.tab })
                },
                SELECT_TABLE: [
                    {
                        guard: ({ event }) => event.table.status === 'occupied' || !!event.tableOrders[event.table.id],
                        target: 'fetchingOrder'
                    },
                    {
                        target: 'redirectingToNewOrder'
                    }
                ],
                SETUP_TABLES: 'settingUp',
                REFRESH_ORDERS: {
                    actions: assign({ tableOrders: ({ event }) => event.tableOrders })
                }
            }
        },
        fetchingOrder: {
            invoke: {
                src: 'fetchOrder',
                input: ({ event }) => event as { table: Table; tableOrders: any },
                onDone: {
                    target: 'viewingOrder',
                    actions: assign({ selectedOrder: ({ event }) => event.output })
                },
                onError: {
                    target: 'idle'
                }
            }
        },
        viewingOrder: {
            on: {
                CLOSE_DETAILS: {
                    target: 'idle',
                    actions: assign({ selectedOrder: null })
                },
                FETCH: 'loading'
            }
        },
        redirectingToNewOrder: {
            always: 'idle'
        },
        settingUp: {
            invoke: {
                src: 'setupTables',
                input: ({ event }) => (event as any).count,
                onDone: {
                    target: 'idle',
                    actions: assign({ tables: ({ event }) => event.output })
                },
                onError: 'error'
            }
        },
        error: {
            on: {
                FETCH: 'loading'
            }
        }
    }
});
