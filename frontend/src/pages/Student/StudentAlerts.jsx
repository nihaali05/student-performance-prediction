import React, { useEffect, useState } from 'react';
import { getWarnings } from '../../services/api';
import RiskBadge from '../../components/RiskBadge';
import { Bell } from 'lucide-react';

const StudentAlerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await getWarnings({ status: 'All' });
        setAlerts(res.data.alerts);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
          <Bell className="w-6 h-6 text-rose-600" />
          <span>Notifications & Risk Warning History</span>
        </h1>
        <p className="text-xs text-purple-700 font-medium mt-1">Rule-based and AI early warning system notifications log.</p>
      </div>

      <div className="glass-panel p-6 space-y-4">
        {loading ? (
          <p className="text-xs text-slate-500 text-center py-6 font-medium">Loading notification log...</p>
        ) : alerts.length === 0 ? (
          <p className="text-xs text-emerald-700 text-center py-6 font-bold">No risk warnings or alerts detected!</p>
        ) : (
          alerts.map((a) => (
            <div key={a.id} className="p-4 rounded-xl bg-purple-50/30 border border-purple-100 flex items-start justify-between gap-4 font-medium">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-xs text-slate-900">{a.warning_type}</span>
                  <RiskBadge level={a.risk_level} size="sm" />
                </div>
                <p className="text-xs text-slate-700">{a.message}</p>
                <p className="text-[11px] text-slate-400 font-mono font-medium">Timestamp: {a.created_at}</p>
              </div>
              <span className={`px-2.5 py-0.5 rounded text-[11px] font-bold ${a.status === 'Active' ? 'bg-rose-100 text-rose-800' : 'bg-slate-100 text-slate-600'}`}>
                {a.status}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default StudentAlerts;
