import React from 'react';

const StatCard = ({ title, value, subtitle, icon: Icon, color = 'purple', trend }) => {
  const colorMap = {
    purple: 'from-purple-50 via-white to-purple-50/30 border-purple-100 text-purple-700 icon-bg-purple',
    indigo: 'from-indigo-50 via-white to-indigo-50/30 border-indigo-100 text-indigo-700 icon-bg-indigo',
    emerald: 'from-emerald-50 via-white to-emerald-50/30 border-emerald-100 text-emerald-700 icon-bg-emerald',
    amber: 'from-amber-50 via-white to-amber-50/30 border-amber-100 text-amber-700 icon-bg-amber',
    rose: 'from-rose-50 via-white to-rose-50/30 border-rose-100 text-rose-700 icon-bg-rose'
  };

  const style = colorMap[color] || colorMap.purple;

  return (
    <div className={`p-5 rounded-2xl bg-gradient-to-br ${style.split(' ')[0]} ${style.split(' ')[1]} ${style.split(' ')[2]} border ${style.split(' ')[3]} backdrop-blur-xl shadow-lg shadow-purple-500/5 relative overflow-hidden transition-all duration-300 hover:scale-[1.02] hover:shadow-xl`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-bold text-slate-500 tracking-wider uppercase">{title}</span>
        {Icon && (
          <div className="p-2.5 rounded-xl bg-purple-100/80 border border-purple-200/60 text-purple-700">
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      <div className="flex items-baseline justify-between">
        <h3 className="text-3xl font-extrabold text-slate-900 tracking-tight">{value}</h3>
        {trend && (
          <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${trend > 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
            {trend > 0 ? `+${trend}%` : `${trend}%`}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="text-xs text-slate-500 mt-2 font-medium">{subtitle}</p>
      )}
    </div>
  );
};

export default StatCard;
