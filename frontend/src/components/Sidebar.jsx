import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard, Users, UserCheck, BarChart3, Cpu,
  GraduationCap, CalendarCheck, FileSpreadsheet, Sparkles, SlidersHorizontal,
  Bell, ClipboardList, FileText, Settings, ShieldAlert, BookOpen
} from 'lucide-react';

const Sidebar = () => {
  const { user } = useAuth();
  if (!user) return null;

  const adminLinks = [
    { to: '/admin/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/admin/students', icon: Users, label: 'Manage Students' },
    { to: '/admin/faculty', icon: UserCheck, label: 'Manage Faculty' },
    { to: '/admin/analytics', icon: BarChart3, label: 'Department Analytics' },
    { to: '/admin/model', icon: Cpu, label: 'ML Model Mgmt' },
    { to: '/settings', icon: Settings, label: 'Settings' }
  ];

  const facultyLinks = [
    { to: '/faculty/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/faculty/students', icon: GraduationCap, label: 'My Students' },
    { to: '/faculty/attendance', icon: CalendarCheck, label: 'Attendance' },
    { to: '/faculty/marks', icon: FileSpreadsheet, label: 'Marks & Exams' },
    { to: '/faculty/predictions', icon: Sparkles, label: 'AI Predictions' },
    { to: '/faculty/at-risk', icon: ShieldAlert, label: 'At-Risk Students' },
    { to: '/faculty/interventions', icon: ClipboardList, label: 'Interventions' },
    { to: '/faculty/reports', icon: FileText, label: 'Reports & Export' },
    { to: '/student/study-assistant', icon: BookOpen, label: 'Study Materials & Quiz' },
    { to: '/settings', icon: Settings, label: 'Settings' }
  ];

  const studentLinks = [
    { to: '/student/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/student/study-assistant', icon: Sparkles, label: 'AI Study Assistant & Quiz' },
    { to: '/student/performance', icon: BarChart3, label: 'My Performance' },
    { to: '/student/prediction', icon: SlidersHorizontal, label: 'What-If Simulator' },
    { to: '/student/recommendations', icon: Sparkles, label: 'AI Recommendations' },
    { to: '/student/alerts', icon: Bell, label: 'Alerts & History' },
    { to: '/settings', icon: Settings, label: 'Settings' }
  ];

  const getLinks = () => {
    switch (user.role) {
      case 'admin': return adminLinks;
      case 'faculty': return facultyLinks;
      case 'student': return studentLinks;
      default: return [];
    }
  };

  const navItems = getLinks();

  return (
    <aside className="w-64 bg-white/90 backdrop-blur-xl border-r border-purple-100 min-h-screen flex flex-col justify-between p-4 sticky top-0 shadow-sm z-20">
      <div>
        {/* Brand Header */}
        <div className="flex items-center gap-3 px-3 py-4 mb-6 border-b border-purple-100">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 via-purple-700 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-500/25">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-wide text-purple-950">EduPredict AI</h1>
            <p className="text-[11px] text-purple-600 font-medium">Early Warning System</p>
          </div>
        </div>

        {/* User Role Tag */}
        <div className="px-3 mb-4">
          <div className="px-3 py-1.5 rounded-xl bg-purple-50/80 border border-purple-100 flex items-center justify-between">
            <span className="text-xs text-purple-700 font-medium">Role:</span>
            <span className="text-xs font-bold uppercase tracking-wider text-purple-700 bg-purple-200/60 px-2 py-0.5 rounded-lg border border-purple-300/60">
              {user.role}
            </span>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-md shadow-purple-500/20 font-semibold'
                      : 'text-slate-600 hover:text-purple-700 hover:bg-purple-50/70'
                  }`
                }
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer Info */}
      <div className="px-3 pt-4 border-t border-purple-100 text-center">
        <p className="text-[11px] text-purple-600 font-medium">v1.0 • White & Purple Edition</p>
      </div>
    </aside>
  );
};

export default Sidebar;
