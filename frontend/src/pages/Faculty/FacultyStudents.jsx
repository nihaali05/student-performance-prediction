import React, { useEffect, useState } from 'react';
import { getStudents } from '../../services/api';
import RiskBadge from '../../components/RiskBadge';
import { Link } from 'react-router-dom';
import { Search, Filter, ArrowRight } from 'lucide-react';

const FacultyStudents = () => {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await getStudents({ search, risk_level: riskFilter });
        setStudents(res.data.students);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [search, riskFilter]);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Assigned Students Roster</h1>
        <p className="text-xs text-purple-700 font-medium mt-1">Select a student profile to inspect SHAP Explainable AI factors and log interventions.</p>
      </div>

      {/* Filters */}
      <div className="glass-panel p-4 flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-purple-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search student name or code..."
            className="w-full bg-purple-50/40 border border-purple-100 text-xs text-slate-800 font-medium pl-9 pr-4 py-2 rounded-xl focus:outline-none focus:border-purple-500"
          />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-purple-600" />
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="bg-purple-50/40 border border-purple-100 text-xs text-slate-800 font-medium px-3 py-2 rounded-xl focus:outline-none focus:border-purple-500"
          >
            <option value="">All Risk Levels</option>
            <option value="GREEN">GREEN (Normal)</option>
            <option value="YELLOW">YELLOW (Needs Attention)</option>
            <option value="ORANGE">ORANGE (At Risk)</option>
            <option value="RED">RED (High Risk)</option>
          </select>
        </div>
      </div>

      {/* Roster Table */}
      <div className="glass-panel p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-purple-900 bg-purple-50/80 uppercase tracking-wider font-bold">
              <tr>
                <th className="p-3">Student Code</th>
                <th className="p-3">Student Name</th>
                <th className="p-3">Department</th>
                <th className="p-3">Semester</th>
                <th className="p-3">GPA</th>
                <th className="p-3">Study Hours</th>
                <th className="p-3">Predicted Score</th>
                <th className="p-3">Risk Level</th>
                <th className="p-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-purple-100 text-slate-700">
              {loading ? (
                <tr>
                  <td colSpan="9" className="p-6 text-center text-slate-500 font-medium">Loading student roster...</td>
                </tr>
              ) : students.map((s) => (
                <tr key={s.id} className="hover:bg-purple-50/40 transition-colors font-medium">
                  <td className="p-3 font-mono text-purple-700 font-bold">{s.student_code}</td>
                  <td className="p-3 font-bold text-slate-900">{s.name}</td>
                  <td className="p-3">{s.department_code}</td>
                  <td className="p-3">Sem {s.semester}</td>
                  <td className="p-3 font-bold text-slate-900">{s.gpa}</td>
                  <td className="p-3">{s.study_hours} hrs/wk</td>
                  <td className="p-3 font-extrabold text-purple-950">{s.predicted_score ? `${s.predicted_score}%` : 'N/A'}</td>
                  <td className="p-3">
                    <RiskBadge level={s.risk_level} size="sm" />
                  </td>
                  <td className="p-3">
                    <Link
                      to={`/faculty/student/${s.id}`}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-100 hover:bg-purple-600 text-purple-800 hover:text-white text-xs font-bold transition-all border border-purple-200"
                    >
                      <span>Deep Profile</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default FacultyStudents;
