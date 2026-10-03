import { useState, useEffect } from 'react';
import api from '../api';
import { toast } from 'react-toastify';
import { Save, Settings as SettingsIcon, Camera, Sliders } from 'lucide-react';

export default function Settings() {
    const [settings, setSettings] = useState({
        CAMERA_INDEX: 0,
        DETECTION_THRESHOLD: 0.6,
        FACE_RECOGNITION_TOLERANCE: 0.5,
        MATCH_THRESHOLD: 3,
        MAX_DISAPPEARANCE_FRAMES: 30
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const res = await api.get('/settings');
                if (res.data) {
                    setSettings(res.data);
                }
            } catch (error) {
                console.error("Failed to fetch settings:", error);
                toast.error("Failed to load settings. Using defaults.");
            } finally {
                setLoading(false);
            }
        };
        fetchSettings();
    }, []);

    const handleChange = (e) => {
        const { name, value, type } = e.target;
        setSettings(prev => ({
            ...prev,
            [name]: type === 'number' || type === 'range' ? Number(value) : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        try {
            await api.post('/settings', settings);
            toast.success("Settings saved successfully!");
        } catch (error) {
            console.error("Failed to save settings:", error);
            toast.error("Failed to save settings.");
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
        );
    }

    return (
        <div className="max-w-3xl mx-auto space-y-8 animate-fade-in">
            <div>
                <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                    <SettingsIcon size={32} className="text-indigo-600" />
                    System Settings
                </h1>
                <p className="text-gray-500 mt-2">Configure camera parameters and facial recognition behavior.</p>
            </div>

            <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-8 space-y-8">
                    
                    {/* Camera Section */}
                    <div className="space-y-5">
                        <div className="flex items-center gap-2 border-b border-gray-100 pb-3">
                            <Camera size={20} className="text-gray-500" />
                            <h3 className="text-lg font-semibold text-gray-800">Camera Configuration</h3>
                        </div>
                        
                        <div className="max-w-md">
                            <label className="block text-sm font-semibold text-gray-700 mb-2">Camera Index</label>
                            <input 
                                type="number" 
                                name="CAMERA_INDEX" 
                                value={settings.CAMERA_INDEX ?? 0} 
                                onChange={handleChange}
                                className="w-full rounded-xl border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow"
                            />
                            <p className="text-sm text-gray-500 mt-2">0 for default webcam, 1 for external USB camera, or provide an IP camera URL string if backend supports it.</p>
                        </div>
                    </div>

                    {/* Recognition Section */}
                    <div className="space-y-5">
                        <div className="flex items-center gap-2 border-b border-gray-100 pb-3">
                            <Sliders size={20} className="text-gray-500" />
                            <h3 className="text-lg font-semibold text-gray-800">Recognition Thresholds</h3>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div className="space-y-2">
                                <label className="block text-sm font-semibold text-gray-700 flex justify-between">
                                    <span>Detection Threshold</span>
                                    <span className="text-indigo-600 font-mono">{settings.DETECTION_THRESHOLD}</span>
                                </label>
                                <input 
                                    type="range" 
                                    step="0.05" min="0" max="1"
                                    name="DETECTION_THRESHOLD" 
                                    value={settings.DETECTION_THRESHOLD ?? 0.6} 
                                    onChange={handleChange}
                                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                                />
                                <p className="text-xs text-gray-500">Confidence required to detect a face.</p>
                            </div>

                            <div className="space-y-2">
                                <label className="block text-sm font-semibold text-gray-700 flex justify-between">
                                    <span>Face Recognition Tolerance</span>
                                    <span className="text-indigo-600 font-mono">{settings.FACE_RECOGNITION_TOLERANCE}</span>
                                </label>
                                <input 
                                    type="range" 
                                    step="0.05" min="0" max="1"
                                    name="FACE_RECOGNITION_TOLERANCE" 
                                    value={settings.FACE_RECOGNITION_TOLERANCE ?? 0.5} 
                                    onChange={handleChange}
                                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                                />
                                <p className="text-xs text-gray-500">Lower value makes recognition more strict (fewer false positives).</p>
                            </div>

                            <div className="space-y-2">
                                <label className="block text-sm font-semibold text-gray-700">Match Threshold (Frames)</label>
                                <input 
                                    type="number" 
                                    min="1"
                                    name="MATCH_THRESHOLD" 
                                    value={settings.MATCH_THRESHOLD ?? 3} 
                                    onChange={handleChange}
                                    className="w-full rounded-xl border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow"
                                />
                                <p className="text-xs text-gray-500 mt-1">Number of consecutive frames required to confirm attendance.</p>
                            </div>

                            <div className="space-y-2">
                                <label className="block text-sm font-semibold text-gray-700">Max Disappearance Frames</label>
                                <input 
                                    type="number" 
                                    min="1"
                                    name="MAX_DISAPPEARANCE_FRAMES" 
                                    value={settings.MAX_DISAPPEARANCE_FRAMES ?? 30} 
                                    onChange={handleChange}
                                    className="w-full rounded-xl border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow"
                                />
                                <p className="text-xs text-gray-500 mt-1">Frames before a person is considered missing from camera view.</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="bg-gray-50 px-8 py-5 border-t border-gray-100 flex justify-end">
                    <button 
                        type="submit" 
                        disabled={saving}
                        className="bg-indigo-600 text-white px-6 py-2.5 rounded-xl font-semibold hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 flex items-center gap-2 transition-all shadow-md shadow-indigo-500/20 disabled:opacity-70 disabled:cursor-not-allowed"
                    >
                        {saving ? (
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        ) : (
                            <Save size={18} />
                        )}
                        {saving ? 'Saving...' : 'Save Settings'}
                    </button>
                </div>
            </form>
        </div>
    );
}
