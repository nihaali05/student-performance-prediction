import React, { useEffect, useState } from 'react';
import { getInterventions } from '../../services/api';
import { ClipboardList, Calendar } from 'lucide-react';

const FacultyInterventions = () => {
  const [interventions, setInterventions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await getInterventions();
        setInterventions(res.data.interventions);
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
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
          <ClipboardList className="w-6 h-6 text-purple-600" />
          <span>Faculty Intervention Management Tracker</span>
        </h1>
        <p className="text-xs text-purple-700 font-medium mt-1">Audit log of academic counseling, parent meetings, and remedial classes.</p>
      </div>

      <div className="glass-panel p-6">
        <div className="space-y-4">
          {loading ? (
            <p className="text-xs text-slate-500 text-center py-6 font-medium">Loading intervention records...</p>
          ) : interventions.length === 0 ? (
            <p className="text-xs text-slate-500 text-center py-6 font-medium">No interventions recorded yet.</p>
          ) : (
            interventions.map((inv) => (
              <div key={inv.id} className="p-5 rounded-2xl bg-purple-50/40 border border-purple-100 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-purple-100 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">{inv.student_name} <span className="font-mono text-purple-700 text-xs font-bold">({inv.student_code})</span></h3>
                    <p className="text-xs text-purple-800 font-bold">{inv.type}</p>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-slate-600 font-medium">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 text-purple-500" />
                      Date: {inv.date}
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                      {inv.status}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-700 font-medium"><strong>Faculty Notes:</strong> {inv.notes}</p>
                {inv.student_response && (
                  <div className="p-3 rounded-xl bg-white border border-purple-100 text-xs text-slate-700 font-medium">
                    <strong className="text-emerald-700">Student Response:</strong> {inv.student_response}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default FacultyInterventions;
