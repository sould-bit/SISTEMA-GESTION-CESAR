
export const DashboardPage = () => {
    return (
        <div className="space-y-6">
            {/* Stats Grid */}
            <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-card-dark rounded-xl p-5 border border-border-dark hover:border-accent-primary/30 transition-all group shadow-sm">
                    <div className="flex justify-between items-start mb-3">
                        <p className="text-text-muted text-sm font-medium">Total Revenue</p>
                        <span className="material-symbols-outlined text-accent-primary bg-accent-primary/10 p-1.5 rounded-md text-[20px]">payments</span>
                    </div>
                    <div className="flex items-end gap-3">
                        <p className="text-white text-3xl font-bold tracking-tight font-mono">$4,240</p>
                        <p className="text-status-success text-xs font-semibold mb-1.5 flex items-center bg-status-success/10 px-1.5 py-0.5 rounded">
                            <span className="material-symbols-outlined text-[14px] mr-0.5">trending_up</span> 12%
                        </p>
                    </div>
                    <p className="text-text-muted text-xs mt-3">Vs. average daily target</p>
                </div>

                <div className="bg-card-dark rounded-xl p-5 border border-border-dark hover:border-accent-primary/30 transition-all group relative overflow-hidden shadow-sm">
                    <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-bl from-accent-primary/5 to-transparent -mr-4 -mt-4 rounded-bl-3xl"></div>
                    <div className="flex justify-between items-start mb-3">
                        <p className="text-text-muted text-sm font-medium">Active Orders</p>
                        <span className="material-symbols-outlined text-white bg-white/5 p-1.5 rounded-md text-[20px]">receipt</span>
                    </div>
                    <div className="flex items-end gap-3">
                        <p className="text-white text-3xl font-bold tracking-tight font-mono">14</p>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-accent-primary/20 text-accent-primary border border-accent-primary/30 tracking-wide">3 PRIORITY</span>
                    </div>
                    <p className="text-text-muted text-xs mt-3">Current kitchen load: <span className="text-white font-medium">85%</span></p>
                </div>

                <div className="bg-card-dark rounded-xl p-5 border border-border-dark hover:border-accent-primary/30 transition-all group shadow-sm">
                    <div className="flex justify-between items-start mb-3">
                        <p className="text-text-muted text-sm font-medium">Avg Prep Time</p>
                        <span className="material-symbols-outlined text-white bg-white/5 p-1.5 rounded-md text-[20px]">timer</span>
                    </div>
                    <div className="flex items-end gap-3">
                        <p className="text-white text-3xl font-bold tracking-tight font-mono">4m 12s</p>
                        <p className="text-status-success text-xs font-semibold mb-1.5 flex items-center bg-status-success/10 px-1.5 py-0.5 rounded">
                            <span className="material-symbols-outlined text-[14px] rotate-180 mr-0.5">trending_up</span> 15s
                        </p>
                    </div>
                    <p className="text-text-muted text-xs mt-3">Target: 4m 30s</p>
                </div>

                <div className="bg-card-dark rounded-xl p-5 border border-border-dark hover:border-accent-primary/30 transition-all group shadow-sm">
                    <div className="flex justify-between items-start mb-3">
                        <p className="text-text-muted text-sm font-medium">Staff on Duty</p>
                        <span className="material-symbols-outlined text-white bg-white/5 p-1.5 rounded-md text-[20px]">badge</span>
                    </div>
                    <div className="flex items-end gap-3">
                        <p className="text-white text-3xl font-bold tracking-tight font-mono">8</p>
                        <span className="text-text-muted text-sm mb-1 font-mono">/ 8</span>
                    </div>
                    <p className="text-status-success text-xs mt-3 font-medium flex items-center gap-1">
                        <span className="size-1.5 rounded-full bg-status-success"></span> Full Capacity
                    </p>
                </div>
            </section>

            {/* Main Content Area */}
            <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Chart Section */}
                <div className="lg:col-span-2 bg-card-dark rounded-xl border border-border-dark p-6 flex flex-col h-full min-h-[350px] shadow-sm">
                    <div className="flex justify-between items-center mb-6">
                        <div>
                            <h3 className="text-white text-lg font-bold">Hourly Sales vs Target</h3>
                            <p className="text-text-muted text-sm mt-1">Today 8:00 AM - 4:00 PM</p>
                        </div>
                        <div className="flex gap-2">
                            <span className="flex items-center gap-2 text-xs text-status-success bg-status-success/10 px-3 py-1.5 rounded-full border border-status-success/20 font-medium">
                                <span className="block size-2 bg-status-success rounded-full animate-pulse"></span> Live Data
                            </span>
                        </div>
                    </div>
                    <div className="flex-1 w-full relative px-2">
                        {/* SVG Chart */}
                        <svg className="w-full h-full overflow-visible" preserveAspectRatio="none" viewBox="0 0 100 50">
                            <defs>
                                <linearGradient id="chartGradient" x1="0" x2="0" y1="0" y2="1">
                                    <stop offset="0%" stopColor="#FF6B00" stopOpacity="0.2"></stop>
                                    <stop offset="100%" stopColor="#FF6B00" stopOpacity="0"></stop>
                                </linearGradient>
                            </defs>
                            <line stroke="#334155" strokeWidth="0.1" x1="0" x2="100" y1="0" y2="0"></line>
                            <line stroke="#334155" strokeDasharray="2" strokeWidth="0.1" x1="0" x2="100" y1="12.5" y2="12.5"></line>
                            <line stroke="#334155" strokeWidth="0.1" x1="0" x2="100" y1="25" y2="25"></line>
                            <line stroke="#334155" strokeDasharray="2" strokeWidth="0.1" x1="0" x2="100" y1="37.5" y2="37.5"></line>
                            <line stroke="#334155" strokeWidth="0.1" x1="0" x2="100" y1="50" y2="50"></line>
                            <path d="M0 45 C 10 40, 20 42, 30 30 C 40 18, 50 25, 60 20 C 70 15, 80 10, 90 12 C 95 13, 100 5, 100 5 L 100 50 L 0 50 Z" fill="url(#chartGradient)"></path>
                            <path d="M0 45 C 10 40, 20 42, 30 30 C 40 18, 50 25, 60 20 C 70 15, 80 10, 90 12 C 95 13, 100 5, 100 5" fill="none" stroke="#FF6B00" strokeWidth="0.6" vectorEffect="non-scaling-stroke"></path>
                            <circle cx="100" cy="5" fill="#FF6B00" r="1.5" stroke="#1E293B" strokeWidth="0.5"></circle>
                        </svg>
                    </div>
                    <div className="flex justify-between text-xs text-text-muted mt-4 font-mono uppercase tracking-wider">
                        <span>8 AM</span>
                        <span>10 AM</span>
                        <span>12 PM</span>
                        <span>2 PM</span>
                        <span>4 PM</span>
                    </div>
                </div>

                {/* Right Column: AI & Alerts */}
                <div className="flex flex-col gap-6">
                    {/* AI Prediction */}
                    <div className="bg-gradient-to-br from-[#1E293B] to-[#0F172A] rounded-xl border border-accent-primary/40 p-5 relative overflow-hidden shadow-[0_0_20px_rgba(255,107,0,0.05)]">
                        <div className="absolute top-0 right-0 p-3 opacity-10">
                            <span className="material-symbols-outlined text-6xl text-white">psychology</span>
                        </div>
                        <div className="flex items-center gap-2 mb-3 relative z-10">
                            <span className="material-symbols-outlined text-accent-primary animate-pulse">auto_awesome</span>
                            <h4 className="text-white font-bold text-sm tracking-wide">AI PREDICTION</h4>
                        </div>
                        <p className="text-gray-300 text-sm leading-relaxed mb-4 relative z-10">
                            Predicted rush incoming in <span className="text-accent-primary font-bold">15 mins</span> based on local event traffic. Suggest preparing 20 extra patties.
                        </p>
                        <div className="w-full bg-black/40 h-1.5 rounded-full overflow-hidden relative z-10">
                            <div className="bg-accent-primary h-full rounded-full w-[92%] shadow-[0_0_10px_#FF6B00]"></div>
                        </div>
                        <p className="text-right text-[10px] text-text-muted mt-2 font-mono relative z-10">CONFIDENCE: 92%</p>
                    </div>

                    {/* Inventory Alerts */}
                    <div className="bg-card-dark rounded-xl border border-border-dark p-5 flex-1 flex flex-col shadow-sm">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-white font-bold text-base">Inventory Alerts</h3>
                            <button className="text-xs text-accent-primary hover:text-white transition-colors font-medium">View All</button>
                        </div>
                        <div className="space-y-3 flex-1">
                            <div className="flex items-center justify-between p-3 rounded-lg bg-bg-deep border border-border-dark hover:border-status-alert/30 transition-colors">
                                <div className="flex items-center gap-3">
                                    <div className="size-9 rounded bg-status-alert/10 flex items-center justify-center text-status-alert border border-status-alert/20">
                                        <span className="material-symbols-outlined text-[18px]">warning</span>
                                    </div>
                                    <div>
                                        <p className="text-white text-sm font-medium">Tomato Slices</p>
                                        <p className="text-status-alert text-xs font-medium">Low Stock (5%)</p>
                                    </div>
                                </div>
                                <button className="px-3 py-1.5 rounded bg-white text-bg-deep text-xs font-bold hover:bg-gray-200 transition-colors">
                                    Reorder
                                </button>
                            </div>
                            <div className="flex items-center justify-between p-3 rounded-lg bg-bg-deep border border-border-dark hover:border-accent-primary/30 transition-colors">
                                <div className="flex items-center gap-3">
                                    <div className="size-9 rounded bg-accent-primary/10 flex items-center justify-center text-accent-primary border border-accent-primary/20">
                                        <span className="material-symbols-outlined text-[18px]">production_quantity_limits</span>
                                    </div>
                                    <div>
                                        <p className="text-white text-sm font-medium">Paper Cups (L)</p>
                                        <p className="text-accent-primary text-xs font-medium">Running Low (12%)</p>
                                    </div>
                                </div>
                                <button className="p-1 rounded text-text-muted hover:text-white hover:bg-white/10">
                                    <span className="material-symbols-outlined text-[18px]">more_vert</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Live Operations Table */}
            <section className="bg-card-dark rounded-xl border border-border-dark flex flex-col overflow-hidden shadow-sm">
                <div className="px-6 py-5 border-b border-border-dark flex flex-wrap gap-4 justify-between items-center bg-card-dark">
                    <div className="flex items-center gap-3">
                        <h3 className="text-white text-lg font-bold">Live Operations</h3>
                        <span className="px-2.5 py-1 rounded-full bg-accent-primary/10 text-accent-primary text-xs font-bold border border-accent-primary/20">5 Pending</span>
                    </div>
                    <div className="flex gap-2">
                        <button className="px-3 py-1.5 rounded-lg bg-bg-deep border border-border-dark text-text-muted text-xs font-medium hover:text-white hover:border-white/20 transition-all flex items-center gap-2">
                            <span className="material-symbols-outlined text-[16px]">filter_list</span> Filter
                        </button>
                        <button className="px-3 py-1.5 rounded-lg bg-bg-deep border border-border-dark text-text-muted text-xs font-medium hover:text-white hover:border-white/20 transition-all flex items-center gap-2">
                            <span className="material-symbols-outlined text-[16px]">download</span> Export
                        </button>
                    </div>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead className="bg-[#182334] text-xs uppercase text-text-muted font-semibold tracking-wider">
                            <tr>
                                <th className="px-6 py-4 border-b border-border-dark w-24">Order ID</th>
                                <th className="px-6 py-4 border-b border-border-dark">Items</th>
                                <th className="px-6 py-4 border-b border-border-dark w-40">Status</th>
                                <th className="px-6 py-4 border-b border-border-dark w-32">Wait Time</th>
                                <th className="px-6 py-4 border-b border-border-dark w-32 text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-dark text-sm">
                            <tr className="hover:bg-white/[0.02] transition-colors group">
                                <td className="px-6 py-4 text-white font-mono">#4091</td>
                                <td className="px-6 py-4 text-gray-300">
                                    <div className="flex flex-col">
                                        <span className="font-medium text-white">2x Dbl Burger, Lg Fries</span>
                                        <span className="text-xs text-text-muted mt-0.5">Note: No pickles</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-status-info/10 text-status-info border border-status-info/20">
                                        <span className="size-1.5 rounded-full bg-status-info animate-pulse"></span> Preparing
                                    </span>
                                </td>
                                <td className="px-6 py-4 font-mono text-gray-300">04:12</td>
                                <td className="px-6 py-4 text-right">
                                    <button className="text-white/70 hover:text-accent-primary text-xs font-bold uppercase tracking-wider transition-colors">View</button>
                                </td>
                            </tr>
                            <tr className="hover:bg-white/[0.02] transition-colors group">
                                <td className="px-6 py-4 text-white font-mono">#4092</td>
                                <td className="px-6 py-4 text-gray-300">
                                    <span className="font-medium text-white">1x Vanilla Shake</span>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-status-success/10 text-status-success border border-status-success/20">
                                        <span className="material-symbols-outlined text-[14px]">check</span> Ready
                                    </span>
                                </td>
                                <td className="px-6 py-4 font-mono text-gray-300">01:45</td>
                                <td className="px-6 py-4 text-right">
                                    <button className="text-accent-primary hover:text-white text-xs font-bold uppercase tracking-wider transition-colors">Serve</button>
                                </td>
                            </tr>
                            <tr className="hover:bg-white/[0.02] transition-colors group">
                                <td className="px-6 py-4 text-white font-mono">#4093</td>
                                <td className="px-6 py-4 text-gray-300">
                                    <span className="font-medium text-white">Fam Bundle A</span>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-accent-primary/10 text-accent-primary border border-accent-primary/20">
                                        <span className="material-symbols-outlined text-[14px]">skillet</span> Cooking
                                    </span>
                                </td>
                                <td className="px-6 py-4 font-mono text-status-alert font-bold">08:30</td>
                                <td className="px-6 py-4 text-right">
                                    <button className="text-white/70 hover:text-accent-primary text-xs font-bold uppercase tracking-wider transition-colors">View</button>
                                </td>
                            </tr>
                            <tr className="hover:bg-white/[0.02] transition-colors group">
                                <td className="px-6 py-4 text-white font-mono">#4094</td>
                                <td className="px-6 py-4 text-gray-300">
                                    <span className="font-medium text-white">Kids Meal (Chkn)</span>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-gray-700/30 text-gray-400 border border-gray-600/30">
                                        Pending
                                    </span>
                                </td>
                                <td className="px-6 py-4 font-mono text-gray-300">00:20</td>
                                <td className="px-6 py-4 text-right">
                                    <button className="bg-accent-primary hover:bg-accent-primary/90 text-white px-3 py-1.5 rounded text-xs font-bold transition-colors shadow-sm">Start</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>
        </div>
    );
};
