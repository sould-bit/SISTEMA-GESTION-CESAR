import { useSocket } from './SocketProvider';

export const NotificationToast = () => {
    const { notifications, clearNotification, isConnected } = useSocket();

    if (notifications.length === 0) return null;

    return (
        <div style={{
            position: 'fixed',
            top: '1rem',
            right: '1rem',
            zIndex: 9999,
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem',
            maxWidth: '400px',
        }}>
            {/* Connection status indicator */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.25rem 0.75rem',
                borderRadius: '1rem',
                backgroundColor: isConnected ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                border: `1px solid ${isConnected ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'}`,
                fontSize: '0.75rem',
                color: isConnected ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
                alignSelf: 'flex-end',
            }}>
                <span style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: isConnected ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
                }}></span>
                {isConnected ? 'En línea' : 'Desconectado'}
            </div>

            {/* Notification cards */}
            {notifications.map((notification) => (
                <div
                    key={notification.id}
                    style={{
                        backgroundColor: 'white',
                        borderRadius: '0.75rem',
                        boxShadow: '0 10px 40px rgba(0, 0, 0, 0.15)',
                        padding: '1rem',
                        borderLeft: '4px solid rgb(59, 130, 246)',
                        animation: 'slideIn 0.3s ease-out',
                    }}
                >
                    <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                    }}>
                        <div>
                            <h4 style={{
                                margin: 0,
                                fontSize: '0.875rem',
                                fontWeight: 600,
                                color: '#1f2937',
                            }}>
                                {notification.title}
                            </h4>
                            <p style={{
                                margin: '0.25rem 0 0',
                                fontSize: '0.875rem',
                                color: '#6b7280',
                            }}>
                                {notification.message}
                            </p>
                            <span style={{
                                fontSize: '0.75rem',
                                color: '#9ca3af',
                            }}>
                                {notification.timestamp.toLocaleTimeString()}
                            </span>
                        </div>
                        <button
                            onClick={() => clearNotification(notification.id)}
                            style={{
                                background: 'none',
                                border: 'none',
                                cursor: 'pointer',
                                padding: '0.25rem',
                                color: '#9ca3af',
                                fontSize: '1.25rem',
                                lineHeight: 1,
                            }}
                        >
                            ×
                        </button>
                    </div>
                </div>
            ))}

            <style>{`
                @keyframes slideIn {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
            `}</style>
        </div>
    );
};
