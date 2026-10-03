import React, { useState, useEffect } from 'react';
import { Play, Square, Video, Clock, UserCheck, AlertCircle } from 'lucide-react';
import api from '../api';
import { toast } from 'react-toastify';

const getStateColor = (state) => {
  switch (state) {
    case 'UNKNOWN': return 'bg-gray-100 text-gray-700 border-gray-200';
    case 'DETECTED': return 'bg-amber-50 text-amber-700 border-amber-200';
    case 'CONFIRMED': return 'bg-blue-50 text-blue-700 border-blue-200';
    case 'PRESENT': return 'bg-green-50 text-green-700 border-green-200';
    default: return 'bg-gray-100 text-gray-700 border-gray-200';
  }
};

const getStateDot = (state) => {
  switch (state) {
    case 'UNKNOWN': return 'bg-gray-500';
    case 'DETECTED': return 'bg-amber-500 animate-pulse';
    case 'CONFIRMED': return 'bg-blue-500';
    case 'PRESENT': return 'bg-green-500';
    default: return 'bg-gray-500';
  }
};

export default function Attendance() {
  const [className, setClassName] = useState('');
  const [isActive, setIsActive] = useState(false);
  const [status, setStatus] = useState({ elapsed: 0, summary: {} });
  const [showSummaryModal, setShowSummaryModal] = useState(false);
  const [finalSummary, setFinalSummary] = useState(null);

  useEffect(() => {
    let interval;
    if (isActive) {
      interval = setInterval(async () => {
        try {
          const res = await api.get('/attendance/status');
          if (res.data.session_active) {
            setStatus(res.data);
          } else {
            // Session was stopped from backend or crashed
            setIsActive(false);
          }
        } catch (err) {
          console.error('Failed to fetch status', err);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [isActive]);

  const handleStart = async () => {
    if (!className.trim()) {
      toast.error('Please enter a class name');
      return;
    }
    try {
      await api.post('/attendance/start', { class_name: className });
      setIsActive(true);
      setStatus({ elapsed: 0, summary: {} });
      toast.success(`Started attendance session for ${className}`);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to start session');
      console.error(err);
    }
  };

  const handleStop = async () => {
    try {
      const res = await api.post('/attendance/stop');
      setFinalSummary(res.data.summary);
      setShowSummaryModal(true);
      setIsActive(false);
      toast.info('Attendance session ended');
    } catch (err) {
      toast.error('Failed to stop session');
      console.error(err);
    }
  };

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Video className="w-6 h-6 text-indigo-600" />
          Live Attendance Session
        </h1>
        <p className="text-gray-500 text-sm mt-1">Start a camera session to automatically mark student attendance.</p>
      </div>

      {!isActive ? (
        <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 max-w-md mx-auto text-center mt-12">
          <div className="w-16 h-16 bg-indigo-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <UserCheck className="w-8 h-8 text-indigo-600" />
          </div>
          <h2 className="text-xl font-semibold mb-6 text-gray-800">Start New Session</h2>
          <div className="space-y-4">
            <div>
              <input
                type="text"
                value={className}
                onChange={(e) => setClassName(e.target.value)}
                placeholder="Enter Class Name (e.g. BSCS-6A)"
                className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-center text-lg shadow-sm"
              />
            </div>
            <button
              onClick={handleStart}
              className="w-full bg-indigo-600 text-white py-3 rounded-lg hover:bg-indigo-700 transition-colors flex items-center justify-center gap-2 font-medium text-lg shadow-sm"
            >
              <Play className="w-5 h-5" fill="currentColor" />
              Start Camera Session
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Camera View */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-gray-900 rounded-xl overflow-hidden relative shadow-lg border border-gray-800 aspect-video flex items-center justify-center">
              <img
                src="/api/attendance/feed"
                alt="Live Attendance Feed"
                className="w-full h-full object-cover"
              />
              <div className="absolute top-4 left-4 bg-black/60 backdrop-blur-sm text-white px-3 py-1.5 rounded-full text-sm font-medium flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
                LIVE REC
              </div>
              <div className="absolute top-4 right-4 bg-black/60 backdrop-blur-sm text-white px-3 py-1.5 rounded-full text-sm font-mono flex items-center gap-2">
                <Clock className="w-4 h-4" />
                {formatTime(status.elapsed || 0)}
              </div>
            </div>
            <div className="flex justify-between items-center bg-white p-4 rounded-xl shadow-sm border border-gray-100">
              <div>
                <h3 className="font-semibold text-gray-800">Session Active: {className}</h3>
                <p className="text-sm text-gray-500">Keep students facing the camera for at least 3 seconds.</p>
              </div>
              <button
                onClick={handleStop}
                className="bg-red-500 text-white px-6 py-2.5 rounded-lg hover:bg-red-600 transition-colors flex items-center gap-2 font-medium shadow-sm"
              >
                <Square className="w-4 h-4" fill="currentColor" />
                Stop Session
              </button>
            </div>
          </div>

          {/* Sidebar Status Panel */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col h-[calc(100vh-12rem)] min-h-[500px]">
            <div className="p-4 border-b border-gray-100 bg-gray-50 rounded-t-xl">
              <h2 className="font-semibold text-gray-800 flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-indigo-600" />
                Recognition Status
              </h2>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {Object.keys(status.summary || {}).length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-gray-400 space-y-2">
                  <AlertCircle className="w-8 h-8 opacity-50" />
                  <p className="text-sm">No students detected yet.</p>
                </div>
              ) : (
                Object.entries(status.summary || {}).map(([name, data]) => (
                  <div key={name} className={`p-3 rounded-lg border flex items-center justify-between ${getStateColor(data.state)} transition-all duration-300`}>
                    <div>
                      <h4 className="font-medium">{name}</h4>
                      <p className="text-xs opacity-75 mt-0.5">
                        Detected {data.detections} times
                      </p>
                    </div>
                    <div className="flex items-center gap-2 bg-white/50 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider">
                      <div className={`w-2 h-2 rounded-full ${getStateDot(data.state)}`}></div>
                      {data.state}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Summary Modal */}
      {showSummaryModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl transform transition-all">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Session Summary</h2>
            <p className="text-gray-500 mb-6">Attendance session for <span className="font-semibold text-gray-700">{className}</span> has ended.</p>
            
            <div className="bg-gray-50 rounded-xl p-4 mb-6 max-h-64 overflow-y-auto">
              {Object.keys(finalSummary || {}).length === 0 ? (
                <p className="text-center text-gray-500 py-4">No students were detected during this session.</p>
              ) : (
                <div className="space-y-2">
                  {Object.entries(finalSummary || {}).map(([name, data]) => (
                    <div key={name} className="flex justify-between items-center py-2 border-b border-gray-200 last:border-0">
                      <span className="font-medium text-gray-800">{name}</span>
                      <span className={`text-sm px-2.5 py-1 rounded-full font-medium ${
                        data.state === 'PRESENT' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
                      }`}>
                        {data.state}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            <div className="flex justify-end">
              <button
                onClick={() => {
                  setShowSummaryModal(false);
                  setClassName('');
                }}
                className="bg-indigo-600 text-white px-6 py-2.5 rounded-lg hover:bg-indigo-700 transition-colors font-medium"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
