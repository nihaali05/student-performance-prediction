import React, { useEffect, useState } from 'react';
import { getFacultyDashboard, getWarnings } from '../../services/api';
import StatCard from '../../components/StatCard';
import RiskBadge from '../../components/RiskBadge';
import { Users, TrendingUp, CalendarCheck, AlertTriangle, ShieldAlert, Bell, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

const FacultyDashboard = () => {
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [statsRes, alertsRes] = await Promise.all([
          getFacultyDashboard(),
          getWarnings({ status: 'Active' })
        ]);
        setStats(statsRes.data);
        setAlerts(alertsRes.data.alerts);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading || !stats) {
    return <div className="p-8 text-center text-slate-500 font-medium">Loading Faculty Dashboard...</div>;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Faculty Class Dashboard</h1>
        <p className="text-xs text-purple-700 font-medium mt-1">
          Assigned Department: <strong className="text-purple-900 font-bold">{stats.department_name}</strong> • Real-time student academic tracking & early warnings.
        </p>
      </div>

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard title="Assigned Students" value={stats.total_assigned_students} icon={Users} color="purple" subtitle="In department cohort" />
        <StatCard title="Class Avg Score" value={`${stats.avg_class_performance}%`} icon={TrendingUp} color="emerald" subtitle="Overall predicted mean" />
        <StatCard title="Avg Attendance" value={`${stats.avg_attendance}%`} icon={CalendarCheck} color="indigo" subtitle="Class attendance record" />
        <StatCard title="High Risk Students" value={stats.high_risk_count} icon={AlertTriangle} color="rose" subtitle="Critical RED warnings" />
      </div>

      {/* Quick Action Grid & Recent Early Warning Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Actions Panel */}
        <div className="glass-panel p-6 space-y-4">
          <h3 className="text-base font-bold text-slate-900 mb-2">Faculty Quick Tools</h3>
          <div className="space-y-2.5">
            <Link
              to="/faculty/attendance"
              className="p-3 rounded-xl bg-purple-50/50 hover:bg-purple-50 border border-purple-100 flex items-center justify-between text-xs font-semibold text-slate-800 transition-all group"
            >
              <div className="flex items-center gap-3">
                <CalendarCheck className="w-4 h-4 text-purple-600" />
                <span>Record Class Attendance</span>
              </div>
              <ArrowRight className="w-4 h-4 text-purple-400 group-hover:translate-x-1 transition-transform" />
            </Link>

            <Link
              to="/faculty/marks"
              className="p-3 rounded-xl bg-purple-50/50 hover:bg-purple-50 border border-purple-100 flex items-center justify-between text-xs font-semibold text-slate-800 transition-all group"
            >
              <div className="flex items-center gap-3">
                <TrendingUp className="w-4 h-4 text-emerald-600" />
                <span>Enter Test / Exam Marks</span>
              </div>
              <ArrowRight className="w-4 h-4 text-purple-400 group-hover:translate-x-1 transition-transform" />
            </Link>

            <Link
              to="/faculty/predictions"
              className="p-3 rounded-xl bg-purple-50/50 hover:bg-purple-50 border border-purple-100 flex items-center justify-between text-xs font-semibold text-slate-800 transition-all group"
            >
              <div className="flex items-center gap-3">
                <ShieldAlert className="w-4 h-4 text-indigo-600" />
                <span>Run AI Prediction Pipeline</span>
              </div>
              <ArrowRight className="w-4 h-4 text-purple-400 group-hover:translate-x-1 transition-transform" />
            </Link>

            <Link
              to="/faculty/interventions"
              className="p-3 rounded-xl bg-purple-50/50 hover:bg-purple-50 border border-purple-100 flex items-center justify-between text-xs font-semibold text-slate-800 transition-all group"
            >
              <div className="flex items-center gap-3">
                <Users className="w-4 h-4 text-amber-600" />
                <span>Log Student Intervention</span>
              </div>
              <ArrowRight className="w-4 h-4 text-purple-400 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>

        {/* Recent Active Early Warning Alerts */}
        <div className="lg:col-span-2 glass-panel p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Bell className="w-5 h-5 text-rose-500" />
              <span>Recent Early Warning Alerts</span>
            </h3>
            <Link to="/faculty/at-risk" className="text-xs font-bold text-purple-700 hover:underline">
              View All At-Risk
            </Link>
          </div>

          <div className="space-y-3">
            {alerts.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center font-medium">No active risk warnings reported.</p>
            ) : (
              alerts.slice(0, 5).map((a) => (
                <div key={a.id} className="p-3.5 rounded-xl bg-purple-50/30 border border-purple-100 flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs text-slate-900">{a.student_name}</span>
                      <span className="text-[11px] font-mono text-purple-700 font-semibold">({a.student_code})</span>
                      <RiskBadge level={a.risk_level} size="sm" />
                    </div>
                    <p className="text-xs text-slate-600 font-medium">{a.message}</p>
                  </div>
                  <Link
                    to={`/faculty/student/${a.student_id}`}
                    className="px-3 py-1.5 rounded-lg bg-purple-100 hover:bg-purple-200 text-purple-800 text-xs font-bold border border-purple-200 whitespace-nowrap transition-all"
                  >
                    View Profile
                  </Link>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FacultyDashboard;
