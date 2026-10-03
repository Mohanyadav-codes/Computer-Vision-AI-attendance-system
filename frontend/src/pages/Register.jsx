import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Camera, Save, UserPlus, Trash2, CheckCircle2 } from 'lucide-react';
import api from '../api';
import { toast } from 'react-toastify';

export default function Register() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    roll_number: '',
    class_name: ''
  });
  const [captures, setCaptures] = useState([]); // { image: base64, encoding: base64 }
  const [isCapturing, setIsCapturing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleCapture = async () => {
    if (captures.length >= 5) {
      toast.warning('Maximum 5 captures reached');
      return;
    }
    
    setIsCapturing(true);
    try {
      const res = await api.post('/register/capture');
      if (res.data.success) {
        setCaptures([...captures, { 
          image: res.data.face_image, 
          encoding: res.data.encoding 
        }]);
        toast.success(`Face captured successfully (${captures.length + 1}/5)`);
      } else {
        toast.error(res.data.message || 'No face detected or error occurred');
      }
    } catch (err) {
      toast.error('Failed to capture face');
      console.error(err);
    } finally {
      setIsCapturing(false);
    }
  };

  const removeCapture = (index) => {
    setCaptures(captures.filter((_, i) => i !== index));
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (captures.length !== 5) {
      toast.error('Please capture exactly 5 face samples');
      return;
    }
    
    setIsSubmitting(true);
    try {
      await api.post('/students/register', {
        name: formData.name,
        roll_number: formData.roll_number,
        class_name: formData.class_name,
        encodings: captures.map(c => c.encoding)
      });
      toast.success('Student registered successfully!');
      navigate('/students');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to register student');
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <UserPlus className="w-6 h-6 text-indigo-600" />
          Register New Student
        </h1>
        <p className="text-gray-500 text-sm mt-1">Fill in the details and capture 5 face samples for accurate recognition.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Side: Form */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 h-fit">
          <h2 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">Student Details</h2>
          <form id="register-form" onSubmit={handleRegister} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
              <input
                type="text"
                name="name"
                required
                value={formData.name}
                onChange={handleInputChange}
                className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                placeholder="e.g. John Doe"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Roll Number</label>
              <input
                type="text"
                name="roll_number"
                required
                value={formData.roll_number}
                onChange={handleInputChange}
                className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                placeholder="e.g. CS2024-001"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Class Name</label>
              <input
                type="text"
                name="class_name"
                required
                value={formData.class_name}
                onChange={handleInputChange}
                className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                placeholder="e.g. BSCS-6A"
              />
            </div>
          </form>
        </div>

        {/* Right Side: Face Capture */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col">
          <h2 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2 flex justify-between items-center">
            Face Capture
            <span className={`text-sm px-2 py-1 rounded-full ${captures.length === 5 ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
              {captures.length} / 5 Captured
            </span>
          </h2>
          
          <div className="bg-gray-900 rounded-lg overflow-hidden relative aspect-video flex items-center justify-center border border-gray-200 shadow-inner">
            <img 
              src="/api/register/feed" 
              alt="Camera Feed" 
              className="w-full h-full object-cover"
              onError={(e) => {
                e.target.style.display = 'none';
                e.target.nextSibling.style.display = 'flex';
              }}
            />
            <div className="absolute inset-0 flex items-center justify-center text-gray-400 hidden flex-col gap-2">
              <Camera className="w-8 h-8" />
              <span>Camera feed unavailable</span>
            </div>
          </div>

          <div className="mt-4 flex justify-center">
            <button
              type="button"
              onClick={handleCapture}
              disabled={isCapturing || captures.length >= 5}
              className={`flex items-center gap-2 px-6 py-2.5 rounded-lg font-medium transition-all ${
                captures.length >= 5 
                  ? 'bg-green-100 text-green-700 cursor-not-allowed'
                  : 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm'
              } disabled:opacity-70`}
            >
              {captures.length >= 5 ? <CheckCircle2 className="w-5 h-5" /> : <Camera className="w-5 h-5" />}
              {isCapturing ? 'Capturing...' : captures.length >= 5 ? 'Done' : 'Capture Face'}
            </button>
          </div>

          {/* Thumbnails */}
          {captures.length > 0 && (
            <div className="mt-6">
              <p className="text-sm font-medium text-gray-600 mb-2">Captured Samples</p>
              <div className="flex gap-3 flex-wrap">
                {captures.map((cap, idx) => (
                  <div key={idx} className="relative group rounded-md overflow-hidden w-16 h-16 border-2 border-indigo-100 shadow-sm">
                    <img src={`data:image/jpeg;base64,${cap.image}`} alt={`Capture ${idx + 1}`} className="w-full h-full object-cover" />
                    <button
                      onClick={() => removeCapture(idx)}
                      className="absolute inset-0 bg-black/50 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <Trash2 className="w-4 h-4 text-red-400" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="mt-8 flex justify-end">
        <button
          type="submit"
          form="register-form"
          disabled={isSubmitting || captures.length !== 5}
          className="flex items-center gap-2 bg-green-600 text-white px-8 py-3 rounded-xl hover:bg-green-700 transition-colors shadow-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed text-lg"
        >
          <Save className="w-5 h-5" />
          {isSubmitting ? 'Registering...' : 'Register Student'}
        </button>
      </div>
    </div>
  );
}
