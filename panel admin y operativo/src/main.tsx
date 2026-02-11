import { registerSW } from 'virtual:pwa-register'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Provider } from 'react-redux'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from 'react-router-dom'
import { store } from './stores/store'
import { router } from './routes/router'
import { SocketProvider } from './components/SocketProvider'
import { NotificationToast } from './components/NotificationToast'
import { SessionInitializer } from './components/auth/SessionInitializer'
import { PWAInstallPrompt } from './components/PWAInstallPrompt'
import '@fontsource/inter/400.css';
import '@fontsource/inter/500.css';
import '@fontsource/inter/600.css';
import '@fontsource/inter/700.css';
import '@fontsource/jetbrains-mono/400.css';
import '@fontsource/jetbrains-mono/500.css';
import './index.css'

const queryClient = new QueryClient()

registerSW({ immediate: true })

createRoot(document.getElementById('root')!).render(
    <StrictMode>
        <Provider store={store}>
            <QueryClientProvider client={queryClient}>
                <SocketProvider>
                    <SessionInitializer />
                    <NotificationToast />
                    <PWAInstallPrompt />
                    <RouterProvider router={router} />
                </SocketProvider>
            </QueryClientProvider>
        </Provider>
    </StrictMode>,
)

