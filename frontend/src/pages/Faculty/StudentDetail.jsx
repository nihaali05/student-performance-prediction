import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getStudentDetail, createIntervention } from '../../services/api';
import RiskBadge from '../../components/RiskBadge';
import { Sparkles, AlertTriangle, ArrowLeft, Plus, CheckCircle2, MessageSquare, ClipboardList } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts';

const StudentDetail = () => {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showInterventionModal, setShowInterventionModal] = useState(false);

  const [invForm, setInvForm] = useState({
    type: 'Academic Counseling & Mentoring',
    notes: '',
    date: new Date().toISOString().split('T')[0],
    student_response: '',
    next_review_date: ''
  });

  const fetchDetail = async () => {
    setLoading(true);
    try {
      const res = await getStudentDetail(id);
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [id]);

  const handleAddIntervention = async (e) => {
    e.preventDefault();
    try {
      await createIntervention({
        student_id: Number(id),
        ...invForm
      });
      setShowInterventionModal(false);
      fetchDetail();
    } catch (err) {
      alert('Failed to log intervention.');
    }
  };

  if (loading || !data) {
    return <div className="p-8 text-center text-slate-500 font-medium">Loading Student AI Profile...</div>;
  }

  const { student, prediction, interventions } = data;
  const xai = prediction.xai || {};

  const radarData = [
    { subject: 'Attendance %', student: student.avg_attendance, benchmark: 75 },
    { subject: 'Internal Marks', student: student.avg_marks, benchmark: 65 },
    { subject: 'Assignments %', student: student.avg_assignments, benchmark: 70 },
    { subject: 'Quizzes %', student: student.avg_quizzes, benchmark: 65 },
    { subject: 'Study Hours x5', student: Math.min(100, student.study_hours * 5), benchmark: 60 }
  ];

  return (
    <div className="space-y-8">
      {/* Back button & Title */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/faculty/students" className="p-2 rounded-xl bg-white border border-purple-200 text-purple-700 hover:bg-purple-50 transition-all shadow-xs">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">{student.name}</h1>
            <p className="text-xs text-purple-700 mt-0.5 font-mono font-semibold">
              Code: <strong className="text-purple-900">{student.student_code}</strong> • Dept: {student.department_name} • Semester {student.semester}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <RiskBadge level={prediction.risk_level} size="lg" />
          <button
            onClick={() => setShowInterventionModal(true)}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-purple-500/20 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Log Intervention</span>
          </button>
        </div>
      </div>

      {/* Top Banner: Predicted Score & ML Confidence */}
      <div className="glass-panel p-6 bg-gradient-to-r from-purple-100/70 via-white to-indigo-50/50 border-l-4 border-l-purple-600 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-1 text-center md:text-left">
          <span className="text-xs font-bold text-purple-700 uppercase tracking-wider flex items-center justify-center md:justify-start gap-1.5">
            <Sparkles className="w-4 h-4" />
            <span>AI Final Performance Forecast</span>
          </span>
          <h2 className="text-4xl font-extrabold text-slate-900 tracking-tight">{prediction.predicted_score}%</h2>
          <p className="text-xs text-slate-600 font-medium">
            Category: <strong className="text-purple-800">{prediction.performance_category}</strong> • Model: {prediction.model_used}
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs bg-white/90 p-4 rounded-2xl border border-purple-100 shadow-sm w-full md:w-auto font-medium">
          <div>
            <span className="text-slate-500 font-semibold">Current GPA</span>
            <p className="text-lg font-bold text-slate-900">{student.gpa}</p>
          </div>
          <div>
            <span className="text-slate-500 font-semibold">Attendance</span>
            <p className="text-lg font-bold text-emerald-600">{student.avg_attendance}%</p>
          </div>
          <div>
            <span className="text-slate-500 font-semibold">Study Hours</span>
            <p className="text-lg font-bold text-purple-700">{student.study_hours} hrs/wk</p>
          </div>
          <div>
            <span className="text-slate-500 font-semibold">Active Backlogs</span>
            <p className="text-lg font-bold text-rose-600">{student.backlogs}</p>
          </div>
        </div>
      </div>

      {/* XAI Explainable AI Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Positive & Negative Factors */}
        <div className="glass-panel p-6 space-y-5">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-600" />
            <span>Explainable AI (SHAP Impact Breakdown)</span>
          </h3>

          <div className="space-y-3">
            <h4 className="text-xs font-bold text-emerald-700 uppercase tracking-wider">Top Positive Factors</h4>
            {xai.positive_factors && xai.positive_factors.length > 0 ? (
              xai.positive_factors.map((f, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span className="font-semibold text-slate-800">{f.name}: <strong>{f.value}</strong></span>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800">
                    {f.impact_level} Positive Impact
                  </span>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-500 font-medium">No significant positive drivers detected.</p>
            )}
          </div>

          <div className="space-y-3 pt-2">
            <h4 className="text-xs font-bold text-rose-700 uppercase tracking-wider">Top Risk & Negative Drivers</h4>
            {xai.negative_factors && xai.negative_factors.length > 0 ? (
              xai.negative_factors.map((f, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-rose-50 border border-rose-200 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-rose-600" />
                    <span className="font-semibold text-slate-800">{f.name}: <strong>{f.value}</strong></span>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-100 text-rose-800">
                    {f.impact_level} Risk Factor
                  </span>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-500 font-medium">No significant risk drivers detected.</p>
            )}
          </div>
        </div>

        {/* Radar Chart Component */}
        <div className="glass-panel p-6">
          <h3 className="text-base font-bold text-slate-900 mb-2">Academic Profile vs Class Benchmark</h3>
          <p className="text-xs text-purple-700 mb-4 font-medium">Radar chart visualizing student metrics against 75th percentile benchmark.</p>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis dataKey="subject" stroke="#475569" tick={{ fontSize: 11 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#cbd5e1" />
                <Radar name="Student" dataKey="student" stroke="#9333ea" fill="#9333ea" fillOpacity={0.4} />
                <Radar name="Class Benchmark" dataKey="benchmark" stroke="#10b981" fill="#10b981" fillOpacity={0.2} />
                <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e9d5ff', borderRadius: '12px', color: '#0f172a', boxShadow: '0 10px 25px -5px rgba(147, 51, 234, 0.1)' }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Intervention History Section */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <ClipboardList className="w-5 h-5 text-purple-600" />
            <span>Faculty Intervention History & Tracked Response</span>
          </h3>
        </div>

        <div className="space-y-3">
          {interventions.length === 0 ? (
            <p className="text-xs text-slate-500 py-4 text-center font-medium">No past intervention records logged for this student.</p>
          ) : (
            interventions.map((inv) => (
              <div key={inv.id} className="p-4 rounded-2xl bg-purple-50/40 border border-purple-100 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs text-purple-800">{inv.type}</span>
                    <span className="text-[11px] text-slate-500 font-medium">• Date: {inv.date}</span>
                    <span className="text-[11px] text-slate-500 font-medium">• By: {inv.faculty_name}</span>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                    {inv.status}
                  </span>
                </div>
                <p className="text-xs text-slate-700 font-medium"><strong>Notes:</strong> {inv.notes}</p>
                {inv.response && (
                  <p className="text-xs text-slate-700 bg-white p-2.5 rounded-xl border border-purple-100 font-medium">
                    <strong className="text-emerald-700">Student Commitment:</strong> {inv.response}
                  </p>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Modal to Add New Intervention */}
      {showInterventionModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white p-6 max-w-lg w-full relative rounded-3xl border border-purple-100 shadow-2xl">
            <h3 className="text-lg font-extrabold text-slate-900 mb-4 flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-purple-600" />
              <span>Log Faculty Intervention Record</span>
            </h3>

            <form onSubmit={handleAddIntervention} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 font-bold mb-1">Intervention Type</label>
                <select
                  value={invForm.type}
                  onChange={(e) => setInvForm({ ...invForm, type: e.target.value })}
                  className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium"
                >
                  <option value="Academic Counseling & Mentoring">Academic Counseling & Mentoring</option>
                  <option value="Extra Class & Remedial Coaching">Extra Class & Remedial Coaching</option>
                  <option value="Parent Meeting">Parent Meeting</option>
                  <option value="Assignment Support & Lab Tutoring">Assignment Support & Lab Tutoring</option>
                  <option value="Backlog Preparatory Support">Backlog Preparatory Support</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Faculty Intervention Notes</label>
                <textarea
                  required
                  rows="3"
                  value={invForm.notes}
                  onChange={(e) => setInvForm({ ...invForm, notes: e.target.value })}
                  placeholder="Details of discussion, identified weaknesses, and remediation strategy..."
                  className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Student Commitment / Feedback</label>
                <textarea
                  rows="2"
                  value={invForm.student_response}
                  onChange={(e) => setInvForm({ ...invForm, student_response: e.target.value })}
                  placeholder="Student's response or commitment plan..."
                  className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium"
                />
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="submit"
                  className="flex-1 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold text-xs shadow-lg shadow-purple-500/20"
                >
                  Save Intervention Record
                </button>
                <button
                  type="button"
                  onClick={() => setShowInterventionModal(false)}
                  className="py-3 px-4 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentDetail;
