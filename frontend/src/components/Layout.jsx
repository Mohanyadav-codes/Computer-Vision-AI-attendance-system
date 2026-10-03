import { NavLink, Outlet } from 'react-router-dom';
import { LayoutDashboard, Users, Video, FileBarChart, Settings } from 'lucide-react';

export default function Layout() {
    const navItems = [
        { name: 'Dashboard', path: '/', icon: LayoutDashboard },
        { name: 'Students', path: '/students', icon: Users },
        { name: 'Attendance', path: '/attendance', icon: Video },
        { name: 'Reports', path: '/reports', icon: FileBarChart },
        { name: 'Settings', path: '/settings', icon: Settings },
    ];

    return (
        <div className="flex h-screen bg-[#F8F9FA] text-gray-800 font-sans">
            {/* Sidebar */}
            <aside className="w-64 bg-[#1E1E2E] text-white flex flex-col shadow-xl z-10">
                <div className="p-6 border-b border-gray-800">
                    <h1 className="text-2xl font-bold tracking-wider text-indigo-500 flex items-center gap-2">
                        <Video size={28} />
                        CV Admin
                    </h1>
                    <p className="text-xs text-gray-400 mt-1">Smart Attendance System</p>
                </div>
                <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        return (
                            <NavLink
                                key={item.path}
                                to={item.path}
                                className={({ isActive }) =>
                                    `flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                                        isActive
                                            ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20'
                                            : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                                    }`
                                }
                            >
                                {({ isActive }) => (
                                    <>
                                        <Icon size={20} className={isActive ? 'text-white' : 'text-gray-400'} />
                                        <span className="font-medium">{item.name}</span>
                                    </>
                                )}
                            </NavLink>
                        );
                    })}
                </nav>
                <div className="p-4 border-t border-gray-800 text-xs text-center text-gray-500">
                    CV Attendance v1.0
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col overflow-hidden bg-[#F8F9FA]">
                <div className="flex-1 overflow-x-hidden overflow-y-auto p-8">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
