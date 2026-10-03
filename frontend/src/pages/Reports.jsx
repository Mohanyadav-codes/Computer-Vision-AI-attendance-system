import React, { useState, useEffect } from 'react';
import { Calendar, Download, Search, FileBarChart, Filter } from 'lucide-react';
import api from '../api';
import { toast } from 'react-toastify';

export default function Reports() {
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [className, setClassName] = useState('');
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const fetchReports = async (e) => {
    if (e) e.preventDefault();
    if (!className.trim()) {
      toast.error('Please enter a class name');
      return;
    }

    setLoading(true);
    setHasSearched(true);
    try {
      const res = await api.get(`/reports/data?date=${date}&class_name=${className}`);
      setRecords(res.data || []);
    } catch (err) {
      toast.error('Failed to fetch reports');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    if (!className.trim()) {
      toast.error('Please enter a class name before exporting');
      return;
    }
    window.open(`http://localhost:5000/api/reports/export?date=${date}&class_name=${className}`, '_blank');
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <FileBarChart className="w-6 h-6 text-indigo-600" />
          Attendance Reports
        </h1>
        <p className="text-gray-500 text-sm mt-1">View and export attendance records for specific classes and dates.</p>
      </div>

      {/* Filter Card */}
      <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 mb-8">
        <form onSubmit={fetchReports} className="flex flex-col md:flex-row gap-4 items-end">
          <div className="flex-1 w-full">
            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-2">
              <Calendar className="w-4 h-4 text-gray-400" /> Date
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
            />
          </div>
          <div className="flex-1 w-full">
            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-400" /> Class Name
            </label>
            <input
              type="text"
              value={className}
              onChange={(e) => setClassName(e.target.value)}
              required
              placeholder="e.g. BSCS-6A"
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
            />
          </div>
          <div className="flex gap-3 w-full md:w-auto">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 md:flex-none flex items-center justify-center gap-2 bg-indigo-600 text-white px-6 py-2.5 rounded-lg hover:bg-indigo-700 transition-colors font-medium shadow-sm disabled:opacity-70"
            >
              <Search className="w-4 h-4" />
              {loading ? 'Searching...' : 'Search'}
            </button>
            <button
              type="button"
              onClick={handleExport}
              className="flex-1 md:flex-none flex items-center justify-center gap-2 bg-white text-gray-700 border border-gray-300 px-6 py-2.5 rounded-lg hover:bg-gray-50 transition-colors font-medium shadow-sm"
            >
              <Download className="w-4 h-4" />
              Export CSV
            </button>
          </div>
        </form>
      </div>

      {/* Results Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-gray-50 border-b border-gray-100 text-gray-600 font-medium">
              <tr>
                <th className="px-6 py-4">Student Name</th>
                <th className="px-6 py-4">Roll Number</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">First Seen</th>
                <th className="px-6 py-4">Total Detections</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-gray-700">
              {loading ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-gray-500">
                    <div className="flex justify-center items-center gap-2">
                      <div className="w-5 h-5 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
                      Loading records...
                    </div>
                  </td>
                </tr>
              ) : !hasSearched ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-gray-500">
                    <Search className="w-8 h-8 mx-auto text-gray-300 mb-2" />
                    <p>Select a date and class, then click Search to view records.</p>
                  </td>
                </tr>
              ) : records.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-gray-500">
                    <p className="text-gray-900 font-medium mb-1">No attendance records found.</p>
                    <p className="text-sm">Try checking a different date or class name.</p>
                  </td>
                </tr>
              ) : (
                records.map((record, index) => (
                  <tr key={index} className="hover:bg-gray-50/50 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900">{record.student_name}</td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        {record.roll_number}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                        record.status === 'PRESENT' 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-red-100 text-red-700'
                      }`}>
                        {record.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-500">
                      {record.first_seen ? new Date(record.first_seen).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'}) : '-'}
                    </td>
                    <td className="px-6 py-4 text-gray-500">
                      {record.detections_count || 0}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
