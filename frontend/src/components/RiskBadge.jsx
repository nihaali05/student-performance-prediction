import React from 'react';
import { AlertTriangle, AlertCircle, CheckCircle, Info } from 'lucide-react';

const RiskBadge = ({ level, showIcon = true, size = 'md' }) => {
  const configs = {
    GREEN: {
      label: 'Normal (Low Risk)',
      bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      icon: CheckCircle
    },
    YELLOW: {
      label: 'Needs Attention',
      bg: 'bg-amber-50 text-amber-700 border-amber-200',
      icon: Info
    },
    ORANGE: {
      label: 'At Risk',
      bg: 'bg-orange-50 text-orange-700 border-orange-200',
      icon: AlertCircle
    },
    RED: {
      label: 'High Risk',
      bg: 'bg-rose-50 text-rose-700 border-rose-200 animate-pulse',
      icon: AlertTriangle
    }
  };

  const config = configs[level] || configs.GREEN;
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs gap-1 font-semibold',
    md: 'px-3 py-1 text-xs font-bold gap-1.5',
    lg: 'px-4 py-1.5 text-sm font-extrabold gap-2'
  };

  return (
    <span className={`inline-flex items-center rounded-full border ${config.bg} ${sizeClasses[size]} shadow-xs`}>
      {showIcon && <Icon className={size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-5 h-5' : 'w-4 h-4'} />}
      {config.label}
    </span>
  );
};

export default RiskBadge;
