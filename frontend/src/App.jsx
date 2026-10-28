import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';

// Layout Components
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

// Pages
import Login from './pages/Login';
import AdminDashboard from './pages/Admin/AdminDashboard';
import AdminStudents from './pages/Admin/AdminStudents';
import AdminFaculty from './pages/Admin/AdminFaculty';
import AdminAnalytics from './pages/Admin/AdminAnalytics';
import AdminModelMgmt from './pages/Admin/AdminModelMgmt';

import FacultyDashboard from './pages/Faculty/FacultyDashboard';
import FacultyStudents from './pages/Faculty/FacultyStudents';
import StudentDetail from './pages/Faculty/StudentDetail';
import FacultyAttendance from './pages/Faculty/FacultyAttendance';
import FacultyMarks from './pages/Faculty/FacultyMarks';
import FacultyPredictions from './pages/Faculty/FacultyPredictions';
import FacultyAtRisk from './pages/Faculty/FacultyAtRisk';
import FacultyInterventions from './pages/Faculty/FacultyInterventions';
import FacultyReports from './pages/Faculty/FacultyReports';

import StudentDashboard from './pages/Student/StudentDashboard';
import StudentPerformance from './pages/Student/StudentPerformance';
import StudentPredictionSimulator from './pages/Student/StudentPredictionSimulator';
import StudentRecommendations from './pages/Student/StudentRecommendations';
import StudentAlerts from './pages/Student/StudentAlerts';
import StudentStudyAssistant from './pages/Student/StudentStudyAssistant';

import Settings from './pages/Settings';

// Protected Route Wrapper
const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="min-h-screen bg-slate-50 flex items-center justify-center text-purple-700 font-bold text-sm">Initializing System...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // Redirect to proper role dashboard if role mismatch
    if (user.role === 'admin') return <Navigate to="/admin/dashboard" replace />;
    if (user.role === 'faculty') return <Navigate to="/faculty/dashboard" replace />;
    return <Navigate to="/student/dashboard" replace />;
  }

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar />
        <main className="p-6 md:p-8 flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
};

// Root Redirect Helper
const RootRedirect = () => {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === 'admin') return <Navigate to="/admin/dashboard" replace />;
  if (user.role === 'faculty') return <Navigate to="/faculty/dashboard" replace />;
  return <Navigate to="/student/dashboard" replace />;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<RootRedirect />} />
          <Route path="/login" element={<Login />} />

          {/* ADMIN ROUTES */}
          <Route path="/admin/dashboard" element={<ProtectedRoute allowedRoles={['admin']}><AdminDashboard /></ProtectedRoute>} />
          <Route path="/admin/students" element={<ProtectedRoute allowedRoles={['admin']}><AdminStudents /></ProtectedRoute>} />
          <Route path="/admin/faculty" element={<ProtectedRoute allowedRoles={['admin']}><AdminFaculty /></ProtectedRoute>} />
          <Route path="/admin/analytics" element={<ProtectedRoute allowedRoles={['admin']}><AdminAnalytics /></ProtectedRoute>} />
          <Route path="/admin/model" element={<ProtectedRoute allowedRoles={['admin']}><AdminModelMgmt /></ProtectedRoute>} />

          {/* FACULTY ROUTES */}
          <Route path="/faculty/dashboard" element={<ProtectedRoute allowedRoles={['faculty', 'admin']}><FacultyDashboard /></ProtectedRoute>} />
          <Route path="/faculty/students" element={<ProtectedRoute allowedRoles={['faculty', 'admin']}><FacultyStudents /></ProtectedRoute>} />
          <Route path="/faculty/student/:id" element={<ProtectedRoute allowedRoles={['faculty', 'admin', 'student']}><StudentDetail /></ProtectedRoute>} />
          <Route path="/faculty/attendance" element={<ProtectedRoute allowedRoles={['faculty', 'admin']}><FacultyAttendance /></ProtectedRoute>} />
          <Route path="/faculty/marks" element={<ProtectedRoute allowedRoles={['faculty', 'admin']}><FacultyMarks /></ProtectedRoute>} />
          <Route path="/faculty/predictions" element={<ProtectedRoute allowedRoles={['faculty', 'admin']}><FacultyPredictions /></ProtectedRoute>} />
          <Route path="/faculty/at-risk" element={<ProtectedRoute allowedRoles={['faculty', 'admin']}><FacultyAtRisk /></ProtectedRoute>} />
          <Route path="/faculty/interventions" element={<ProtectedRoute allowedRoles={['faculty', 'admin']}><FacultyInterventions /></ProtectedRoute>} />
          <Route path="/faculty/reports" element={<ProtectedRoute allowedRoles={['faculty', 'admin']}><FacultyReports /></ProtectedRoute>} />

          {/* STUDENT ROUTES */}
          <Route path="/student/dashboard" element={<ProtectedRoute allowedRoles={['student']}><StudentDashboard /></ProtectedRoute>} />
          <Route path="/student/study-assistant" element={<ProtectedRoute allowedRoles={['student', 'faculty', 'admin']}><StudentStudyAssistant /></ProtectedRoute>} />
          <Route path="/student/performance" element={<ProtectedRoute allowedRoles={['student']}><StudentPerformance /></ProtectedRoute>} />
          <Route path="/student/prediction" element={<ProtectedRoute allowedRoles={['student']}><StudentPredictionSimulator /></ProtectedRoute>} />
          <Route path="/student/recommendations" element={<ProtectedRoute allowedRoles={['student']}><StudentRecommendations /></ProtectedRoute>} />
          <Route path="/student/alerts" element={<ProtectedRoute allowedRoles={['student']}><StudentAlerts /></ProtectedRoute>} />

          {/* COMMON SETTINGS */}
          <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />

          {/* FALLBACK */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
