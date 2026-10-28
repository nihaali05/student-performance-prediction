import React, { useEffect, useState } from 'react';
import { getStudents } from '../../services/api';
import RiskBadge from '../../components/RiskBadge';
import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowRight } from 'lucide-react';

const FacultyAtRisk = () => {
  const [atRiskStudents, setAtRiskStudents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [redRes, orangeRes] = await Promise.all([
          getStudents({ risk_level: 'RED' }),
          getStudents({ risk_level: 'ORANGE' })
        ]);
        setAtRiskStudents([...redRes.data.students, ...orangeRes.data.students]);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-rose-600" />
            <span>At-Risk & High-Risk Priority Queue</span>
          </h1>
          <p className="text-xs text-purple-700 font-medium mt-1">Filtered list of students requiring immediate academic counseling or parent notification.</p>
        </div>
      </div>

      <div className="glass-panel p-6 border-l-4 border-l-rose-500">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-purple-900 bg-purple-50/80 uppercase tracking-wider font-bold">
              <tr>
                <th className="p-3">Code</th>
                <th className="p-3">Student Name</th>
                <th className="p-3">Department</th>
                <th className="p-3">GPA</th>
                <th className="p-3">Study Hours</th>
                <th className="p-3">Backlogs</th>
                <th className="p-3">Predicted Score</th>
                <th className="p-3">Risk Status</th>
                <th className="p-3">Intervention</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-purple-100 text-slate-700 font-medium">
              {loading ? (
                <tr>
                  <td colSpan="9" className="p-6 text-center text-slate-500">Scanning risk database...</td>
                </tr>
              ) : atRiskStudents.length === 0 ? (
                <tr>
                  <td colSpan="9" className="p-6 text-center text-emerald-600 font-bold">No high-risk students found! All clear.</td>
                </tr>
              ) : (
                atRiskStudents.map((s) => (
                  <tr key={s.id} className="hover:bg-purple-50/40">
                    <td className="p-3 font-mono text-purple-700 font-bold">{s.student_code}</td>
                    <td className="p-3 font-bold text-slate-900">{s.name}</td>
                    <td className="p-3">{s.department_code}</td>
                    <td className="p-3 font-bold text-rose-600">{s.gpa}</td>
                    <td className="p-3 text-slate-800 font-semibold">{s.study_hours} hrs</td>
                    <td className="p-3 font-bold text-rose-600">{s.backlogs}</td>
                    <td className="p-3 font-extrabold text-rose-600 text-sm">{s.predicted_score}%</td>
                    <td className="p-3">
                      <RiskBadge level={s.risk_level} size="sm" />
                    </td>
                    <td className="p-3">
                      <Link
                        to={`/faculty/student/${s.id}`}
                        className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-rose-100 hover:bg-rose-600 text-rose-800 hover:text-white text-xs font-bold transition-all border border-rose-200"
                      >
                        <span>Take Action</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
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
};

export default FacultyAtRisk;
