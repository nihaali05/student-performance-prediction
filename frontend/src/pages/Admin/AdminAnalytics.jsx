import React, { useEffect, useState } from 'react';
import { getAdminAnalytics } from '../../services/api';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ZAxis } from 'recharts';

const AdminAnalytics = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await getAdminAnalytics();
        setData(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading || !data) {
    return <div className="p-8 text-center text-slate-500 font-medium">Loading deep analytics...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Institutional Deep Analytics</h1>
        <p className="text-xs text-purple-700 font-medium mt-1">Multivariate correlation analysis: Study hours vs GPA vs Predicted Score.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scatter Plot: Study Hours vs Predicted Score */}
        <div className="glass-panel p-6">
          <h3 className="text-base font-bold text-slate-900 mb-2">Study Hours vs Predicted Score Correlation</h3>
          <p className="text-xs text-slate-500 mb-4 font-medium">Each point represents a student profile color-mapped by risk classification.</p>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis type="number" dataKey="study_hours" name="Weekly Study Hours" unit=" hrs" stroke="#64748b" />
                <YAxis type="number" dataKey="predicted_score" name="Predicted Score" unit="%" domain={[30, 100]} stroke="#64748b" />
                <ZAxis type="number" range={[60, 60]} />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e9d5ff', borderRadius: '12px', color: '#0f172a', boxShadow: '0 10px 25px -5px rgba(147, 51, 234, 0.1)' }}
                />
                <Scatter name="Students" data={data.scatter_data} fill="#9333ea" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* GPA vs Predicted Score */}
        <div className="glass-panel p-6">
          <h3 className="text-base font-bold text-slate-900 mb-2">Cumulative GPA vs Final Score Prediction</h3>
          <p className="text-xs text-slate-500 mb-4 font-medium">Assessing academic momentum and consistency across semesters.</p>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis type="number" dataKey="gpa" name="Current GPA" domain={[3, 10]} stroke="#64748b" />
                <YAxis type="number" dataKey="predicted_score" name="Predicted Score" unit="%" domain={[30, 100]} stroke="#64748b" />
                <ZAxis type="number" range={[60, 60]} />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e9d5ff', borderRadius: '12px', color: '#0f172a', boxShadow: '0 10px 25px -5px rgba(147, 51, 234, 0.1)' }}
                />
                <Scatter name="Students" data={data.scatter_data} fill="#10b981" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminAnalytics;
