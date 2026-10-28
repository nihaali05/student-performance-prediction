import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Sparkles, ShieldCheck, GraduationCap, UserCheck, Lock, Mail, ArrowRight } from 'lucide-react';

const Login = () => {
  const [email, setEmail] = useState('admin@analytics.edu');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const userData = await login(email, password);
      if (userData.role === 'admin') navigate('/admin/dashboard');
      else if (userData.role === 'faculty') navigate('/faculty/dashboard');
      else navigate('/student/dashboard');
    } catch (err) {
      if (err.response?.data?.message) {
        setError(err.response.data.message);
      } else if (err.message && (err.message.includes('Network Error') || !err.response)) {
        setError('Cannot connect to backend server. Render may be waking up (takes ~30-50s) or request was blocked by CORS. Please try again in a few moments.');
      } else {
        setError(err.message || 'Unable to connect to server.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemo = (demoEmail, demoPass) => {
    setEmail(demoEmail);
    setPassword(demoPass);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-50 relative overflow-hidden">
      {/* Background Purple Texture Glows */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-300/30 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-300/30 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md bg-white/95 backdrop-blur-xl p-8 rounded-3xl border border-purple-100 shadow-2xl shadow-purple-500/10 relative z-10">
        {/* Title Header */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-purple-600 via-purple-700 to-indigo-600 flex items-center justify-center mx-auto mb-4 shadow-xl shadow-purple-500/30">
            <Sparkles className="w-7 h-7 text-white" />
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Student Performance AI</h2>
          <p className="text-xs text-purple-600 font-medium mt-1">Predictive Analytics & Early Warning Platform</p>
        </div>

        {error && (
          <div className="mb-6 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-purple-400" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@analytics.edu"
                className="w-full bg-purple-50/40 border border-purple-100 text-sm text-slate-900 pl-10 pr-4 py-2.5 rounded-xl focus:outline-none focus:border-purple-500 focus:bg-white focus:ring-2 focus:ring-purple-500/10 transition-all font-medium"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-purple-400" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-purple-50/40 border border-purple-100 text-sm text-slate-900 pl-10 pr-4 py-2.5 rounded-xl focus:outline-none focus:border-purple-500 focus:bg-white focus:ring-2 focus:ring-purple-500/10 transition-all font-medium"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 via-purple-700 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold text-sm shadow-lg shadow-purple-500/25 transition-all flex items-center justify-center gap-2 mt-2 disabled:opacity-50"
          >
            {loading ? 'Authenticating...' : (
              <>
                <span>Sign In to Dashboard</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Quick Role Switcher */}
        <div className="mt-8 pt-6 border-t border-purple-100">
          <p className="text-[11px] font-bold text-purple-800 uppercase tracking-wider mb-3 text-center">Quick Role Switch (One-Click Demo)</p>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => handleQuickDemo('admin@analytics.edu', 'admin123')}
              className="p-2.5 rounded-xl bg-purple-50/80 hover:bg-purple-100 border border-purple-200/80 flex flex-col items-center gap-1 transition-all text-center group"
            >
              <ShieldCheck className="w-4 h-4 text-purple-700 group-hover:scale-110 transition-transform" />
              <span className="text-[11px] font-bold text-purple-900">Admin</span>
            </button>

            <button
              type="button"
              onClick={() => handleQuickDemo('prof.smith@analytics.edu', 'faculty123')}
              className="p-2.5 rounded-xl bg-purple-50/80 hover:bg-purple-100 border border-purple-200/80 flex flex-col items-center gap-1 transition-all text-center group"
            >
              <UserCheck className="w-4 h-4 text-purple-700 group-hover:scale-110 transition-transform" />
              <span className="text-[11px] font-bold text-purple-900">Faculty</span>
            </button>

            <button
              type="button"
              onClick={() => handleQuickDemo('alex.jones@student.edu', 'student123')}
              className="p-2.5 rounded-xl bg-purple-50/80 hover:bg-purple-100 border border-purple-200/80 flex flex-col items-center gap-1 transition-all text-center group"
            >
              <GraduationCap className="w-4 h-4 text-purple-700 group-hover:scale-110 transition-transform" />
              <span className="text-[11px] font-bold text-purple-900">Student</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
