import React, { useEffect, useState } from 'react';
import { getModelStatus, retrainMLModels } from '../../services/api';
import { RefreshCw, CheckCircle2, Award } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const AdminModelMgmt = () => {
  const [modelData, setModelData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [retraining, setRetraining] = useState(false);

  const fetchModelInfo = async () => {
    setLoading(true);
    try {
      const res = await getModelStatus();
      setModelData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModelInfo();
  }, []);

  const handleRetrain = async () => {
    setRetraining(true);
    try {
      const res = await retrainMLModels();
      setModelData(res.data.metadata);
      alert(`ML Retrain Successful! Active Champion Model: ${res.data.best_model} (R² = ${res.data.best_r2})`);
    } catch (err) {
      alert(err.response?.data?.message || 'Failed to retrain models.');
    } finally {
      setRetraining(false);
    }
  };

  if (loading || !modelData) {
    return <div className="p-8 text-center text-slate-500 font-medium">Loading ML Model Engine details...</div>;
  }

  const bestMetrics = modelData.metrics[modelData.best_model_name] || {};
  const featureChartData = Object.entries(bestMetrics.feature_importances || {}).map(([key, val]) => ({
    feature: key.replace('_', ' ').toUpperCase(),
    importance: Math.round(val * 1000) / 10
  })).sort((a, b) => b.importance - a.importance);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Machine Learning Model Management</h1>
          <p className="text-xs text-purple-700 font-medium mt-1">Compare model accuracy, feature importances, evaluation metrics (RMSE, R², MAE), and trigger automated retraining.</p>
        </div>
        <button
          onClick={handleRetrain}
          disabled={retraining}
          className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-purple-500/20 transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${retraining ? 'animate-spin' : ''}`} />
          <span>{retraining ? 'Retraining Models...' : 'Retrain ML Models'}</span>
        </button>
      </div>

      {/* Active Champion Model Banner */}
      <div className="glass-panel p-6 border-l-4 border-l-purple-600 bg-gradient-to-r from-purple-50/80 via-white to-purple-50/40">
        <div className="flex items-center gap-3 mb-2">
          <Award className="w-6 h-6 text-amber-500" />
          <h2 className="text-lg font-bold text-slate-900">Active Champion Model: {modelData.best_model_name}</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4 pt-4 border-t border-purple-100 text-xs">
          <div>
            <span className="text-slate-500 font-semibold">Model Accuracy (R² Score):</span>
            <p className="text-2xl font-extrabold text-emerald-600">{modelData.best_r2}</p>
          </div>
          <div>
            <span className="text-slate-500 font-semibold">Root Mean Squared Error (RMSE):</span>
            <p className="text-2xl font-extrabold text-purple-700">{bestMetrics.rmse || 'N/A'}</p>
          </div>
          <div>
            <span className="text-slate-500 font-semibold">Mean Absolute Error (MAE):</span>
            <p className="text-2xl font-extrabold text-indigo-700">{bestMetrics.mae || 'N/A'}</p>
          </div>
        </div>
      </div>

      {/* Model Performance Comparison Table */}
      <div className="glass-panel p-6">
        <h3 className="text-base font-bold text-slate-900 mb-4">Model Metrics Evaluation Comparison</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-purple-900 bg-purple-50/80 uppercase tracking-wider font-bold">
              <tr>
                <th className="p-3">Model Name</th>
                <th className="p-3">R² Score (Accuracy)</th>
                <th className="p-3">RMSE</th>
                <th className="p-3">MAE</th>
                <th className="p-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-purple-100 text-slate-700">
              {Object.entries(modelData.metrics).map(([name, metrics]) => {
                const isChampion = name === modelData.best_model_name;
                return (
                  <tr key={name} className={isChampion ? 'bg-purple-50/60 font-semibold' : 'hover:bg-purple-50/20'}>
                    <td className="p-3 text-slate-900 font-bold flex items-center gap-2">
                      {isChampion && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
                      <span>{name}</span>
                    </td>
                    <td className="p-3 font-bold text-emerald-600">{metrics.r2}</td>
                    <td className="p-3">{metrics.rmse}</td>
                    <td className="p-3">{metrics.mae}</td>
                    <td className="p-3">
                      {isChampion ? (
                        <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-700 border border-emerald-200">
                          Active Model
                        </span>
                      ) : (
                        <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-500">
                          Candidate
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Global Feature Importance Chart */}
      <div className="glass-panel p-6">
        <h3 className="text-base font-bold text-slate-900 mb-2">Global Feature Importance (Model Weighting)</h3>
        <p className="text-xs text-slate-500 mb-4 font-medium">Features with higher importance heavily influence final predicted student scores and risk triggers.</p>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={featureChartData} layout="vertical" margin={{ left: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis type="number" unit="%" stroke="#64748b" />
              <YAxis type="category" dataKey="feature" stroke="#475569" tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e9d5ff', borderRadius: '12px', color: '#0f172a', boxShadow: '0 10px 25px -5px rgba(147, 51, 234, 0.1)' }}
              />
              <Bar dataKey="importance" fill="#9333ea" radius={[0, 8, 8, 0]}>
                {featureChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={index === 0 ? '#10b981' : index === 1 ? '#9333ea' : '#a855f7'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default AdminModelMgmt;
