import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getStudentDetail } from '../../services/api';
import StatCard from '../../components/StatCard';
import RiskBadge from '../../components/RiskBadge';
import { Sparkles, CalendarCheck, BookOpen, Clock, AlertTriangle, ArrowRight, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

const StudentDashboard = () => {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      if (user && user.student_id) {
        try {
          const res = await getStudentDetail(user.student_id);
          setData(res.data);
        } catch (err) {
          console.error(err);
        } finally {
          setLoading(false);
        }
      } else {
        setLoading(false);
      }
    };
    load();
  }, [user]);

  if (loading) {
    return <div className="p-8 text-center text-slate-500 font-medium">Loading Student Dashboard...</div>;
  }

  if (!data) {
    return <div className="p-8 text-center text-slate-500 font-medium">Student profile data unavailable.</div>;
  }

  const { student, prediction } = data;
  const xai = prediction.xai || {};

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="glass-panel p-6 bg-gradient-to-r from-purple-100/70 via-white to-indigo-50/50 border-l-4 border-l-purple-600 flex flex-col sm:flex-row items-center justify-between gap-6">
        <div>
          <span className="text-xs font-bold text-purple-700 uppercase tracking-wider">Student Portal</span>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight mt-1">Welcome back, {student.name}!</h1>
          <p className="text-xs text-purple-900 font-mono font-semibold mt-1">
            Code: {student.student_code} • {student.department_name} • Semester {student.semester}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <RiskBadge level={prediction.risk_level} size="lg" />
        </div>
      </div>

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard title="Current GPA" value={student.gpa} icon={BookOpen} color="purple" subtitle={`Previous: ${student.prev_gpa}`} />
        <StatCard title="Attendance" value={`${student.avg_attendance}%`} icon={CalendarCheck} color="emerald" subtitle="Overall percentage" />
        <StatCard title="Study Hours" value={`${student.study_hours} hrs`} icon={Clock} color="indigo" subtitle="Weekly self-study" />
        <StatCard title="Predicted Final Score" value={`${prediction.predicted_score}%`} icon={Sparkles} color="amber" subtitle={`Confidence: ${prediction.confidence}%`} />
      </div>

      {/* Main Grid: Recommendations & What-If Simulator Banner */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* AI Recommendations Panel */}
        <div className="lg:col-span-2 glass-panel p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-600" />
              <span>Smart Personalized AI Recommendations</span>
            </h3>
            <Link to="/student/recommendations" className="text-xs font-bold text-purple-700 hover:underline">
              View All
            </Link>
          </div>

          <div className="space-y-3">
            {xai.negative_factors && xai.negative_factors.length > 0 ? (
              xai.negative_factors.map((f, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-purple-50/40 border border-purple-100 flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <span className="text-xs font-bold text-amber-800 uppercase tracking-wider flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                      Priority Focus Area: {f.name}
                    </span>
                    <p className="text-xs text-slate-700 font-medium">
                      Current metric is <strong>{f.value}</strong>. Improving this metric will significantly boost your predicted score.
                    </p>
                  </div>
                  <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-200 whitespace-nowrap">
                    Action Needed
                  </span>
                </div>
              ))
            ) : (
              <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold flex items-center gap-2">
                <ShieldCheck className="w-4 h-4" />
                <span>Great work! Your current metrics are well above benchmark targets.</span>
              </div>
            )}
          </div>
        </div>

        {/* Grounded AI Study Assistant & Quiz Banner Card */}
        <div className="lg:col-span-3 glass-panel p-6 bg-gradient-to-r from-indigo-900 via-purple-900 to-purple-800 text-white rounded-2xl shadow-xl flex flex-col md:flex-row items-center justify-between gap-6 border border-purple-400/30">
          <div className="space-y-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-white/20 text-purple-100 backdrop-blur-md">
              New Grounded RAG AI Feature
            </span>
            <h3 className="text-xl font-extrabold text-white mt-2">AI Study Assistant & Automated Quiz Generator</h3>
            <p className="text-xs text-purple-200 max-w-2xl">
              Upload your PDF chapters or study images. Get zero-hallucination answers with page citations and take AI quizzes generated strictly from your study materials.
            </p>
          </div>
          <Link
            to="/student/study-assistant"
            className="px-5 py-3 rounded-xl bg-white hover:bg-purple-50 text-purple-900 font-bold text-xs shadow-lg transition flex items-center gap-2 whitespace-nowrap"
          >
            <BookOpen className="w-4 h-4 text-purple-700" />
            <span>Open AI Study Assistant</span>
            <ArrowRight className="w-4 h-4 text-purple-700" />
          </Link>
        </div>

        {/* What-If Simulator Quick Card */}
        <div className="lg:col-span-3 glass-panel p-6 flex flex-col md:flex-row items-center justify-between gap-4 bg-gradient-to-br from-purple-50/60 to-indigo-50/40 border border-purple-100">
          <div>
            <div className="w-10 h-10 rounded-xl bg-purple-100 border border-purple-200 flex items-center justify-center text-purple-700 mb-2 shadow-xs">
              <Sparkles className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-slate-900">What-If Performance Simulator</h3>
            <p className="text-xs text-slate-600 font-medium leading-relaxed">
              Test scenario outcomes by adjusting your study hours, attendance, and exam target scores to see live predicted final marks.
            </p>
          </div>

          <Link
            to="/student/prediction"
            className="px-5 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-purple-500/20 transition-all whitespace-nowrap"
          >
            <span>Launch What-If Simulator</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
};

export default StudentDashboard;
