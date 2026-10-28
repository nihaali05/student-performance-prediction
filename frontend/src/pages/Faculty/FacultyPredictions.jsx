import React, { useEffect, useState } from 'react';
import { getStudents, runBatchPredictions } from '../../services/api';
import RiskBadge from '../../components/RiskBadge';
import { Sparkles, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

const FacultyPredictions = () => {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  const fetchStudents = async () => {
    setLoading(true);
    try {
      const res = await getStudents();
      setStudents(res.data.students);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, []);

  const handleRunBatch = async () => {
    setRunning(true);
    try {
      const res = await runBatchPredictions();
      alert(res.data.message);
      fetchStudents();
    } catch (err) {
      alert('Failed to execute prediction pipeline.');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">AI Predictions & Early Warning Engine</h1>
          <p className="text-xs text-purple-700 font-medium mt-1">Automated Machine Learning predictions, risk level scoring, and confidence intervals.</p>
        </div>
        <button
          onClick={handleRunBatch}
          disabled={running}
          className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-purple-500/20 transition-all disabled:opacity-50"
        >
          <Sparkles className={`w-4 h-4 ${running ? 'animate-spin' : ''}`} />
          <span>{running ? 'Running Pipeline...' : 'Run Batch AI Predictions'}</span>
        </button>
      </div>

      <div className="glass-panel p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-purple-900 bg-purple-50/80 uppercase tracking-wider font-bold">
              <tr>
                <th className="p-3">Student Code</th>
                <th className="p-3">Name</th>
                <th className="p-3">Predicted Final Score</th>
                <th className="p-3">Performance Category</th>
                <th className="p-3">Model Confidence</th>
                <th className="p-3">Risk Classification</th>
                <th className="p-3">Explainability</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-purple-100 text-slate-700 font-medium">
              {loading ? (
                <tr>
                  <td colSpan="7" className="p-6 text-center text-slate-500">Loading AI predictions...</td>
                </tr>
              ) : (
                students.map((s) => (
                  <tr key={s.id} className="hover:bg-purple-50/40">
                    <td className="p-3 font-mono text-purple-700 font-bold">{s.student_code}</td>
                    <td className="p-3 font-bold text-slate-900">{s.name}</td>
                    <td className="p-3 font-extrabold text-purple-950 text-sm">{s.predicted_score}%</td>
                    <td className="p-3 font-bold text-slate-800">{s.performance_category}</td>
                    <td className="p-3 font-bold text-emerald-600">{s.confidence}%</td>
                    <td className="p-3">
                      <RiskBadge level={s.risk_level} size="sm" />
                    </td>
                    <td className="p-3">
                      <Link
                        to={`/faculty/student/${s.id}`}
                        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-purple-100 hover:bg-purple-600 text-purple-800 hover:text-white text-xs font-bold transition-all border border-purple-200"
                      >
                        <span>View SHAP XAI</span>
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

export default FacultyPredictions;
