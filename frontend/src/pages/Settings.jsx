import React, { useState } from 'react';
import { Settings as SettingsIcon, Save, Shield, Bell } from 'lucide-react';

const Settings = () => {
  const [thresholds, setThresholds] = useState({
    attendance_warning: 65,
    academic_warning: 40,
    high_risk_score: 50,
    assignment_warning: 60,
    email_notifications: true
  });

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-purple-600" />
          <span>System Settings & Risk Threshold Configurations</span>
        </h1>
        <p className="text-xs text-purple-700 font-medium mt-1">Configure automated Early Warning Engine rule triggers and platform preferences.</p>
      </div>

      <div role="status" className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-medium">
        Settings are not currently persisted. Changes on this page are temporary and will be lost when you leave; the backend does not provide a settings save API.
      </div>

      <div className="space-y-6">
        {/* Risk Thresholds Panel */}
        <div className="glass-panel p-6 space-y-4">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-purple-100 pb-3">
            <Shield className="w-5 h-5 text-purple-600" />
            <span>Early Warning Rule Thresholds</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-medium">
            <div>
              <label className="block text-slate-700 font-bold mb-1">Attendance Warning Trigger (%)</label>
              <input
                type="number"
                value={thresholds.attendance_warning}
                onChange={(e) => setThresholds({ ...thresholds, attendance_warning: Number(e.target.value) })}
                className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium"
              />
              <span className="text-[11px] text-slate-500 font-medium">Attendance below this % triggers Attendance Warning.</span>
            </div>

            <div>
              <label className="block text-slate-700 font-bold mb-1">Academic Pass Benchmark (%)</label>
              <input
                type="number"
                value={thresholds.academic_warning}
                onChange={(e) => setThresholds({ ...thresholds, academic_warning: Number(e.target.value) })}
                className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium"
              />
              <span className="text-[11px] text-slate-500 font-medium">Marks below this score trigger Academic Warning.</span>
            </div>

            <div>
              <label className="block text-slate-700 font-bold mb-1">High Risk Prediction Cutoff Score</label>
              <input
                type="number"
                value={thresholds.high_risk_score}
                onChange={(e) => setThresholds({ ...thresholds, high_risk_score: Number(e.target.value) })}
                className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium"
              />
              <span className="text-[11px] text-slate-500 font-medium">Predicted final score below this triggers RED High Risk.</span>
            </div>

            <div>
              <label className="block text-slate-700 font-bold mb-1">Assignment Completion Target (%)</label>
              <input
                type="number"
                value={thresholds.assignment_warning}
                onChange={(e) => setThresholds({ ...thresholds, assignment_warning: Number(e.target.value) })}
                className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium"
              />
              <span className="text-[11px] text-slate-500 font-medium">Completion rate below this triggers Assignment Warning.</span>
            </div>
          </div>
        </div>

        {/* Notifications & System Preferences */}
        <div className="glass-panel p-6 space-y-4">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-purple-100 pb-3">
            <Bell className="w-5 h-5 text-purple-600" />
            <span>Alert & Notification System</span>
          </h3>

          <div className="flex items-center justify-between text-xs font-medium">
            <div>
              <p className="font-bold text-slate-900">Automated In-App & Email Notifications</p>
              <p className="text-slate-500 text-[11px]">Send automatic alerts when a student transitions into ORANGE or RED risk levels.</p>
            </div>
            <input
              type="checkbox"
              checked={thresholds.email_notifications}
              onChange={(e) => setThresholds({ ...thresholds, email_notifications: e.target.checked })}
              className="w-5 h-5 accent-purple-600 rounded cursor-pointer"
            />
          </div>
        </div>

        <button
          type="button"
          disabled
          title="Settings persistence is not available."
          className="px-6 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-purple-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Save className="w-4 h-4" />
          <span>Saving Unavailable</span>
        </button>
      </div>
    </div>
  );
};

export default Settings;
