import { useAppDispatch, useAppSelector } from '../../stores/store';
import { logout } from '../../stores/auth.slice';
import { toggleSidebar } from '../../stores/ui.slice';
import { useNavigate, useLocation } from 'react-router-dom';

export const Header = () => {
    const dispatch = useAppDispatch();
    const navigate = useNavigate();
    const location = useLocation();

    // Hide back button only on main dashboard
    const isRootPage = location.pathname === '/admin/dashboard' || location.pathname === '/genesis';

    const user = useAppSelector(state => state.auth.user);
    const userInitials = user?.username ? user.username.substring(0, 2).toUpperCase() : 'JD';
    const userRole = user?.role_name || user?.role || 'User';

    const handleLogout = () => {
        dispatch(logout());
        navigate('/login');
    };

    return (
        <header className="h-16 border-b border-border-dark bg-bg-deep/90 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between shrink-0 z-10 sticky top-0">
            <div className="flex items-center gap-2 sm:gap-6 min-w-0">
                <button
                    className="lg:hidden text-white hover:text-accent-primary transition-colors p-2 -ml-2 active:bg-white/10 rounded-lg flex items-center justify-center"
                    onClick={() => dispatch(toggleSidebar())}
                >
                    <span className="material-symbols-outlined">menu</span>
                </button>

                {!isRootPage && (
                    <button
                        onClick={() => navigate(-1)}
                        className="flex items-center justify-center text-text-muted hover:text-white transition-colors hover:bg-white/10 rounded-full p-1"
                        title="Atrás"
                    >
                        <span className="material-symbols-outlined">arrow_back</span>
                    </button>
                )}

                <div className="flex items-center gap-2 text-white min-w-0">
                    <span className="material-symbols-outlined text-accent-primary shrink-0">storefront</span>
                    <h2 className="text-xs sm:text-sm font-semibold tracking-wide text-white/90 truncate">Store #402 - Downtown Seattle</h2>
                </div>
                <div className="hidden md:flex h-6 w-px bg-border-dark mx-2"></div>
                <div className="hidden md:flex items-center bg-card-dark border border-border-dark rounded-lg px-3 py-1.5 w-80 focus-within:border-accent-primary/50 transition-colors group">
                    <span className="material-symbols-outlined text-text-muted text-[20px] group-focus-within:text-white transition-colors">search</span>
                    <input
                        className="bg-transparent border-none text-sm text-white placeholder-text-muted focus:ring-0 w-full ml-2 font-sans h-full py-0 focus:outline-none"
                        placeholder="Search orders, items, or staff..."
                        type="text"
                    />
                </div>
            </div>
            <div className="flex items-center gap-2 sm:gap-6 shrink-0">
                <button className="relative text-text-muted hover:text-white transition-colors p-1.5 active:bg-white/10 rounded-lg">
                    <span className="material-symbols-outlined">notifications</span>
                    <span className="absolute top-1 right-1 size-2 bg-accent-primary rounded-full border-2 border-bg-deep"></span>
                </button>
                <div className="flex items-center gap-2 sm:gap-3 sm:pl-6 sm:border-l border-border-dark cursor-pointer hover:bg-white/5 p-1.5 sm:p-2 rounded-lg transition-colors" onClick={handleLogout}>
                    <div className="text-right hidden sm:block">
                        <p className="text-sm font-medium text-white leading-none">{user?.username || 'Jane Doe'}</p>
                        <p className="text-xs text-text-muted mt-1 leading-none">{userRole}</p>
                    </div>
                    {/* Placeholder Avatar */}
                    <div className="size-9 rounded-full bg-card-dark border border-border-dark flex items-center justify-center text-text-muted text-sm font-bold">
                        {userInitials}
                    </div>
                </div>
            </div>
        </header>
    );
};
