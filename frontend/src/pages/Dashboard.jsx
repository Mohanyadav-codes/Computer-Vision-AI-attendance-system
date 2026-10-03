import { useState, useEffect } from 'react';
import api from '../api';
import { Users, UserCheck, UserX, Clock } from 'lucide-react';

export default function Dashboard() {
    const [stats, setStats] = useState({ total_students: 0, today_present: 0, today_absent: 0, classes: [] });
    const [recentAttendance, setRecentAttendance] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                // For stats endpoint
                const statsRes = await api.get('/stats').catch(() => ({ data: { total_students: 0, today_present: 0, today_absent: 0, classes: [] } }));
                
                // For reports endpoint
                const today = new Date().toISOString().split('T')[0];
                const attendanceRes = await api.get(`/reports/data?date=${today}`).catch(() => ({ data: [] }));
                
                setStats(statsRes.data);
                setRecentAttendance(attendanceRes.data || []);
            } catch (error) {
                console.error("Failed to fetch dashboard data:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchDashboardData();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
        );
    }

    const statCards = [
        { title: 'Total Students', value: stats.total_students, icon: Users, color: 'bg-blue-500', bgColor: 'bg-blue-50' },
        { title: 'Present Today', value: stats.today_present, icon: UserCheck, color: 'bg-emerald-500', bgColor: 'bg-emerald-50' },
        { title: 'Absent Today', value: stats.today_absent, icon: UserX, color: 'bg-rose-500', bgColor: 'bg-rose-50' },
        { title: 'Active Classes', value: stats.classes?.length || 0, icon: Clock, color: 'bg-indigo-500', bgColor: 'bg-indigo-50' },
    ];

    return (
        <div className="space-y-8 animate-fade-in">
            <div>
                <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
                <p className="text-gray-500 mt-1">Overview of today's attendance and system status.</p>
            </div>
            
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {statCards.map((stat, index) => {
                    const Icon = stat.icon;
                    return (
                        <div key={index} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 flex items-center gap-5 transition-transform hover:-translate-y-1 duration-200">
                            <div className={`${stat.bgColor} p-4 rounded-xl`}>
                                <Icon size={28} className={`text-${stat.color.split('-')[1]}-600`} style={{ color: stat.color.includes('blue') ? '#3B82F6' : stat.color.includes('emerald') ? '#10B981' : stat.color.includes('rose') ? '#F43F5E' : '#6366F1' }} />
                            </div>
                            <div>
                                <p className="text-sm font-medium text-gray-500">{stat.title}</p>
                                <h3 className="text-3xl font-bold text-gray-900 mt-1">{stat.value}</h3>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Recent Attendance Table */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="px-6 py-5 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                    <h2 className="text-lg font-semibold text-gray-900">Recent Attendance (Today)</h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-gray-600">
                        <thead className="bg-gray-50 text-gray-700 uppercase text-xs font-semibold tracking-wider">
                            <tr>
                                <th className="px-6 py-4">Student ID</th>
                                <th className="px-6 py-4">Name</th>
                                <th className="px-6 py-4">Time In</th>
                                <th className="px-6 py-4">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {recentAttendance.length > 0 ? (
                                recentAttendance.map((record, i) => (
                                    <tr key={i} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4 font-mono text-gray-500">{record.student_id}</td>
                                        <td className="px-6 py-4 font-medium text-gray-900">{record.name}</td>
                                        <td className="px-6 py-4 text-gray-500">{record.time_in || '-'}</td>
                                        <td className="px-6 py-4">
                                            <span className={`px-3 py-1 rounded-full text-xs font-medium tracking-wide ${
                                                record.status === 'PRESENT' ? 'bg-emerald-100 text-emerald-700 border border-emerald-200' :
                                                'bg-gray-100 text-gray-700 border border-gray-200'
                                            }`}>
                                                {record.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan="4" className="px-6 py-12 text-center text-gray-400">
                                        <div className="flex flex-col items-center justify-center space-y-2">
                                            <UserX size={32} className="text-gray-300" />
                                            <p>No attendance records found for today.</p>
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
