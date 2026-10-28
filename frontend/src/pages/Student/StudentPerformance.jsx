import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getStudentDetail } from '../../services/api';
import { TrendingUp, CalendarCheck } from 'lucide-react';

const StudentPerformance = () => {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const load = async () => {
      if (user && user.student_id) {
        try {
          const res = await getStudentDetail(user.student_id);
          setData(res.data);
        } catch (err) {
          console.error(err);
          setError(true);
        } finally {
          setLoading(false);
        }
      }
    };
    load();
  }, [user]);

  if (!user?.student_id) {
    return <div role="status" className="p-8 text-center text-slate-600 font-medium">Performance records are unavailable because this account is not linked to a student profile.</div>;
  }

  if (loading) {
    return <div className="p-8 text-center text-slate-500 font-medium">Loading Performance Breakdown...</div>;
  }

  if (error || !data) {
    return <div role="alert" className="p-8 text-center text-slate-600 font-medium">Performance records are unavailable. Please try again later.</div>;
  }

  const { marks_history, attendance_history } = data;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Academic Performance Records</h1>
        <p className="text-xs text-purple-700 font-medium mt-1">Detailed subject-wise breakdown of exam scores, attendance percentages, and assignments.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Marks History */}
        <div className="glass-panel p-6 space-y-4">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-emerald-600" />
            <span>Exam & Internal Marks History</span>
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-purple-900 bg-purple-50/80 uppercase font-bold">
                <tr>
                  <th className="p-2.5">Date</th>
                  <th className="p-2.5">Subject</th>
                  <th className="p-2.5">Test Type</th>
                  <th className="p-2.5">Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-purple-100 text-slate-700 font-medium">
                {marks_history.map((m) => (
                  <tr key={m.id} className="hover:bg-purple-50/30">
                    <td className="p-2.5 font-mono text-slate-500">{m.date}</td>
                    <td className="p-2.5 font-bold text-slate-900">{m.subject_name}</td>
                    <td className="p-2.5 text-purple-700 font-bold">{m.test_type}</td>
                    <td className="p-2.5 font-bold text-emerald-600">{m.score}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Attendance History */}
        <div className="glass-panel p-6 space-y-4">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <CalendarCheck className="w-5 h-5 text-purple-600" />
            <span>Attendance Log</span>
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-purple-900 bg-purple-50/80 uppercase font-bold">
                <tr>
                  <th className="p-2.5">Date</th>
                  <th className="p-2.5">Subject</th>
                  <th className="p-2.5">Status</th>
                  <th className="p-2.5">Cumulative %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-purple-100 text-slate-700 font-medium">
                {attendance_history.map((a) => (
                  <tr key={a.id} className="hover:bg-purple-50/30">
                    <td className="p-2.5 font-mono text-slate-500">{a.date}</td>
                    <td className="p-2.5 font-bold text-slate-900">{a.subject_name}</td>
                    <td className="p-2.5">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${a.status === 'Present' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}`}>
                        {a.status}
                      </span>
                    </td>
                    <td className="p-2.5 font-bold text-slate-900">{a.percentage}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentPerformance;
