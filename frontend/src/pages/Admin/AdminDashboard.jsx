import React, { useEffect, useState } from 'react';
import { getAdminAnalytics } from '../../services/api';
import StatCard from '../../components/StatCard';
import RiskBadge from '../../components/RiskBadge';
import { Users, UserCheck, Building2, TrendingUp, AlertTriangle, ArrowUpRight, ArrowDownRight, RefreshCw } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

const AdminDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const res = await getAdminAnalytics();
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center gap-3 text-purple-700">
          <RefreshCw className="w-6 h-6 animate-spin" />
          <span className="text-sm font-bold">Loading Analytics Dashboard...</span>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-8">
      {/* Page Title Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Admin Executive Dashboard</h1>
          <p className="text-xs text-purple-700 font-medium mt-1">Real-time institutional performance, student risk distributions, and department metrics.</p>
        </div>
        <button
          onClick={fetchAnalytics}
          className="px-4 py-2 rounded-xl bg-white hover:bg-purple-50 text-purple-700 text-xs font-bold flex items-center gap-2 border border-purple-200 shadow-sm transition-all"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh Data</span>
        </button>
      </div>

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard title="Total Students" value={data.total_students} icon={Users} color="purple" subtitle="Active enrolled students" />
        <StatCard title="Total Faculty" value={data.total_faculty} icon={UserCheck} color="indigo" subtitle="Teaching & academic staff" />
        <StatCard title="Departments" value={data.total_departments} icon={Building2} color="emerald" subtitle="Active academic branches" />
        <StatCard title="Avg Performance" value={`${data.avg_performance}%`} icon={TrendingUp} color="amber" subtitle="Institutional ML benchmark" />
      </div>

      {/* Risk Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="glass-panel p-5 border-l-4 border-l-rose-500">
          <div className="flex items-center justify-between text-rose-700 mb-1">
            <span className="text-xs font-extrabold uppercase tracking-wider">High Risk Students</span>
            <AlertTriangle className="w-4 h-4" />
          </div>
          <p className="text-3xl font-extrabold text-slate-900">{data.high_risk_students}</p>
          <p className="text-xs text-slate-500 mt-1 font-medium">Requires immediate intervention</p>
        </div>

        <div className="glass-panel p-5 border-l-4 border-l-orange-500">
          <div className="flex items-center justify-between text-orange-700 mb-1">
            <span className="text-xs font-extrabold uppercase tracking-wider">Total At-Risk</span>
            <AlertTriangle className="w-4 h-4" />
          </div>
          <p className="text-3xl font-extrabold text-slate-900">{data.at_risk_students}</p>
          <p className="text-xs text-slate-500 mt-1 font-medium">ORANGE & RED risk levels</p>
        </div>

        <div className="glass-panel p-5 border-l-4 border-l-emerald-500">
          <div className="flex items-center justify-between text-emerald-700 mb-1">
            <span className="text-xs font-extrabold uppercase tracking-wider">Improving Students</span>
            <ArrowUpRight className="w-4 h-4" />
          </div>
          <p className="text-3xl font-extrabold text-slate-900">{data.improving_students}</p>
          <p className="text-xs text-slate-500 mt-1 font-medium">High performers (&gt;= 75 score)</p>
        </div>

        <div className="glass-panel p-5 border-l-4 border-l-amber-500">
          <div className="flex items-center justify-between text-amber-700 mb-1">
            <span className="text-xs font-extrabold uppercase tracking-wider">Declining Students</span>
            <ArrowDownRight className="w-4 h-4" />
          </div>
          <p className="text-3xl font-extrabold text-slate-900">{data.declining_students}</p>
          <p className="text-xs text-slate-500 mt-1 font-medium">Negative score trend</p>
        </div>
      </div>

      {/* Visual Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution Pie Chart */}
        <div className="glass-panel p-6">
          <h3 className="text-base font-bold text-slate-900 mb-4">Risk Distribution Breakdown</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.risk_distribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {data.risk_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e9d5ff', borderRadius: '12px', color: '#0f172a', boxShadow: '0 10px 25px -5px rgba(147, 51, 234, 0.1)' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-purple-100">
            {data.risk_distribution.map((item, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-xs text-slate-600 font-medium">{item.name}: <strong className="text-slate-900 font-bold">{item.value}</strong></span>
              </div>
            ))}
          </div>
        </div>

        {/* Department Performance Bar Chart */}
        <div className="glass-panel p-6">
          <h3 className="text-base font-bold text-slate-900 mb-4">Department Average Scores</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.department_analytics}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="code" stroke="#64748b" />
                <YAxis domain={[0, 100]} stroke="#64748b" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e9d5ff', borderRadius: '12px', color: '#0f172a', boxShadow: '0 10px 25px -5px rgba(147, 51, 234, 0.1)' }}
                />
                <Bar dataKey="avg_score" fill="#9333ea" radius={[8, 8, 0, 0]} name="Avg Score (%)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Department Analytics Table */}
      <div className="glass-panel p-6">
        <h3 className="text-base font-bold text-slate-900 mb-4">Department Level Risk Summary</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-purple-900 bg-purple-50/80 uppercase tracking-wider font-bold">
              <tr>
                <th className="p-3">Department Code</th>
                <th className="p-3">Department Name</th>
                <th className="p-3">Total Students</th>
                <th className="p-3">Average Predicted Score</th>
                <th className="p-3">At-Risk Count</th>
                <th className="p-3">Health Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-purple-100 text-slate-700">
              {data.department_analytics.map((dept) => (
                <tr key={dept.id} className="hover:bg-purple-50/40 font-medium">
                  <td className="p-3 font-bold text-purple-700">{dept.code}</td>
                  <td className="p-3 font-semibold text-slate-900">{dept.name}</td>
                  <td className="p-3">{dept.student_count}</td>
                  <td className="p-3 font-bold text-slate-900">{dept.avg_score}%</td>
                  <td className="p-3 font-bold text-rose-600">{dept.at_risk_count}</td>
                  <td className="p-3">
                    <RiskBadge level={dept.at_risk_count > 2 ? 'RED' : dept.at_risk_count > 0 ? 'YELLOW' : 'GREEN'} size="sm" />
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

export default AdminDashboard;
