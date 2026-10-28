import React, { useState } from 'react';
import { runWhatIfSimulation } from '../../services/api';
import RiskBadge from '../../components/RiskBadge';
import { SlidersHorizontal, Sparkles, AlertCircle, RefreshCw } from 'lucide-react';

const StudentPredictionSimulator = () => {
  const [params, setParams] = useState({
    attendance: 75.0,
    internal_marks: 65.0,
    assignment_score: 70.0,
    quiz_score: 65.0,
    study_hours: 12.0,
    prev_gpa: 7.0,
    backlogs: 0
  });

  const [simulation, setSimulation] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const res = await runWhatIfSimulation(params);
      setSimulation(res.data.simulation);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
          <SlidersHorizontal className="w-6 h-6 text-purple-600" />
          <span>Interactive What-If Prediction Simulator</span>
        </h1>
        <p className="text-xs text-purple-700 font-medium mt-1">
          Adjust sliders to model hypothetical academic scenarios. See how study habits and attendance directly impact AI predictions.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Sliders Form */}
        <div className="glass-panel p-6 space-y-5">
          <h3 className="text-xs font-bold text-purple-900 uppercase tracking-wider">Scenario Inputs</h3>

          {/* Attendance Slider */}
          <div>
            <div className="flex justify-between text-xs font-bold mb-1">
              <span className="text-slate-700">Attendance Percentage</span>
              <span className="text-emerald-700">{params.attendance}%</span>
            </div>
            <input
              type="range"
              min="30"
              max="100"
              value={params.attendance}
              onChange={(e) => setParams({ ...params, attendance: Number(e.target.value) })}
              className="w-full accent-purple-600 bg-purple-100 cursor-pointer"
            />
          </div>

          {/* Internal Marks Slider */}
          <div>
            <div className="flex justify-between text-xs font-bold mb-1">
              <span className="text-slate-700">Internal Exam Score</span>
              <span className="text-purple-700">{params.internal_marks}%</span>
            </div>
            <input
              type="range"
              min="20"
              max="100"
              value={params.internal_marks}
              onChange={(e) => setParams({ ...params, internal_marks: Number(e.target.value) })}
              className="w-full accent-purple-600 bg-purple-100 cursor-pointer"
            />
          </div>

          {/* Study Hours Slider */}
          <div>
            <div className="flex justify-between text-xs font-bold mb-1">
              <span className="text-slate-700">Weekly Self-Study Hours</span>
              <span className="text-indigo-700">{params.study_hours} hrs</span>
            </div>
            <input
              type="range"
              min="1"
              max="35"
              value={params.study_hours}
              onChange={(e) => setParams({ ...params, study_hours: Number(e.target.value) })}
              className="w-full accent-indigo-600 bg-purple-100 cursor-pointer"
            />
          </div>

          {/* Assignment Score Slider */}
          <div>
            <div className="flex justify-between text-xs font-bold mb-1">
              <span className="text-slate-700">Assignment Completion Score</span>
              <span className="text-amber-700">{params.assignment_score}%</span>
            </div>
            <input
              type="range"
              min="20"
              max="100"
              value={params.assignment_score}
              onChange={(e) => setParams({ ...params, assignment_score: Number(e.target.value) })}
              className="w-full accent-amber-600 bg-purple-100 cursor-pointer"
            />
          </div>

          {/* Backlogs */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Active Backlogs</label>
            <select
              value={params.backlogs}
              onChange={(e) => setParams({ ...params, backlogs: Number(e.target.value) })}
              className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-xs text-slate-900 font-medium"
            >
              <option value={0}>0 Backlogs</option>
              <option value={1}>1 Backlog</option>
              <option value={2}>2 Backlogs</option>
              <option value={3}>3+ Backlogs</option>
            </select>
          </div>

          <button
            onClick={handleSimulate}
            disabled={loading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold text-xs shadow-lg shadow-purple-500/20 transition-all flex items-center justify-center gap-2"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            <span>Run Model Simulation</span>
          </button>
        </div>

        {/* Output Panel */}
        <div className="glass-panel p-6 flex flex-col justify-between space-y-4 border-l-4 border-l-purple-600">
          <div>
            <h3 className="text-xs font-bold text-purple-900 uppercase tracking-wider mb-4">Simulated AI Outcome</h3>

            {simulation ? (
              <div className="space-y-6">
                <div className="p-5 rounded-2xl bg-purple-50/50 border border-purple-100 text-center shadow-inner">
                  <span className="text-xs font-bold text-purple-700 uppercase">Simulated Final Score</span>
                  <h2 className="text-5xl font-extrabold text-slate-900 tracking-tight my-2">{simulation.predicted_score}%</h2>
                  <p className="text-xs text-slate-700 font-bold">Category: <strong className="text-purple-800">{simulation.performance_category}</strong></p>
                </div>

                <div className="flex items-center justify-between p-3.5 rounded-xl bg-white border border-purple-100 text-xs shadow-xs font-medium">
                  <span className="text-slate-700 font-bold">Simulated Risk Level:</span>
                  <RiskBadge level={simulation.risk_level} size="md" />
                </div>

                <div className="flex items-center justify-between p-3.5 rounded-xl bg-white border border-purple-100 text-xs shadow-xs font-medium">
                  <span className="text-slate-700 font-bold">Confidence Interval:</span>
                  <span className="font-extrabold text-emerald-600">{simulation.confidence}%</span>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-slate-500 text-xs font-medium">
                Click "Run Model Simulation" to calculate your projected performance score.
              </div>
            )}
          </div>

          <div className="p-3.5 rounded-xl bg-purple-50/40 border border-purple-100 text-[11px] text-slate-600 font-medium flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-purple-600 shrink-0 mt-0.5" />
            <span>
              Disclaimer: Model-based scenario projection only. Calculated using trained Machine Learning feature weights, not a guaranteed outcome.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentPredictionSimulator;
