import React, { useEffect, useState } from 'react';
import { getStudents, createStudent } from '../../services/api';
import RiskBadge from '../../components/RiskBadge';
import { Search, Plus, Filter, UserPlus, X } from 'lucide-react';

const AdminStudents = () => {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [showModal, setShowModal] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    student_code: '',
    department_id: 1,
    semester: 3,
    gpa: 7.0,
    prev_gpa: 7.0,
    study_hours: 12.0,
    backlogs: 0,
    attendance: 80.0,
    internal_marks: 70.0
  });

  const fetchStudentsList = async () => {
    setLoading(true);
    try {
      const res = await getStudents({ search, risk_level: riskFilter });
      setStudents(res.data.students);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudentsList();
  }, [search, riskFilter]);

  const handleAddStudent = async (e) => {
    e.preventDefault();
    try {
      await createStudent(formData);
      setShowModal(false);
      fetchStudentsList();
    } catch (err) {
      alert(err.response?.data?.message || 'Error creating student.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Student Management Directory</h1>
          <p className="text-xs text-purple-700 font-medium mt-1">View, search, filter, and register new student profiles across departments.</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-purple-500/20 transition-all self-start"
        >
          <Plus className="w-4 h-4" />
          <span>Add New Student</span>
        </button>
      </div>

      {/* Filters Toolbar */}
      <div className="glass-panel p-4 flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-purple-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by student name or code..."
            className="w-full bg-purple-50/40 border border-purple-100 text-xs text-slate-800 pl-9 pr-4 py-2 rounded-xl focus:outline-none focus:border-purple-500 font-medium"
          />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-purple-600" />
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="bg-purple-50/40 border border-purple-100 text-xs text-slate-800 font-medium px-3 py-2 rounded-xl focus:outline-none focus:border-purple-500"
          >
            <option value="">All Risk Levels</option>
            <option value="GREEN">GREEN (Normal)</option>
            <option value="YELLOW">YELLOW (Needs Attention)</option>
            <option value="ORANGE">ORANGE (At Risk)</option>
            <option value="RED">RED (High Risk)</option>
          </select>
        </div>
      </div>

      {/* Student List Table */}
      <div className="glass-panel p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-purple-900 bg-purple-50/80 uppercase tracking-wider font-bold">
              <tr>
                <th className="p-3">Student Code</th>
                <th className="p-3">Name</th>
                <th className="p-3">Department</th>
                <th className="p-3">Semester</th>
                <th className="p-3">GPA</th>
                <th className="p-3">Study Hrs/Wk</th>
                <th className="p-3">Backlogs</th>
                <th className="p-3">Predicted Score</th>
                <th className="p-3">Category</th>
                <th className="p-3">Risk Level</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-purple-100 text-slate-700">
              {loading ? (
                <tr>
                  <td colSpan="10" className="p-6 text-center text-slate-500 font-medium">Loading student directory...</td>
                </tr>
              ) : students.length === 0 ? (
                <tr>
                  <td colSpan="10" className="p-6 text-center text-slate-500 font-medium">No students found matching filters.</td>
                </tr>
              ) : (
                students.map((s) => (
                  <tr key={s.id} className="hover:bg-purple-50/40 font-medium transition-colors">
                    <td className="p-3 font-mono text-purple-700 font-bold">{s.student_code}</td>
                    <td className="p-3 font-bold text-slate-900">{s.name}</td>
                    <td className="p-3">{s.department_code}</td>
                    <td className="p-3">Sem {s.semester}</td>
                    <td className="p-3 font-bold text-slate-900">{s.gpa}</td>
                    <td className="p-3">{s.study_hours} hrs</td>
                    <td className="p-3">{s.backlogs}</td>
                    <td className="p-3 font-extrabold text-purple-950">{s.predicted_score ? `${s.predicted_score}%` : 'N/A'}</td>
                    <td className="p-3 font-semibold text-slate-800">{s.performance_category}</td>
                    <td className="p-3">
                      <RiskBadge level={s.risk_level} size="sm" />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Student Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white p-6 max-w-lg w-full relative rounded-3xl border border-purple-100 shadow-2xl">
            <button
              onClick={() => setShowModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-800"
            >
              <X className="w-5 h-5" />
            </button>
            <h3 className="text-lg font-extrabold text-slate-900 mb-4 flex items-center gap-2">
              <UserPlus className="w-5 h-5 text-purple-600" />
              <span>Register New Student</span>
            </h3>

            <form onSubmit={handleAddStudent} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Full Name</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium"
                    placeholder="e.g. John Doe"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Email</label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium"
                    placeholder="student@edu.com"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Student Code</label>
                  <input
                    type="text"
                    required
                    value={formData.student_code}
                    onChange={(e) => setFormData({ ...formData, student_code: e.target.value })}
                    className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium"
                    placeholder="STU-2001"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Department</label>
                  <select
                    value={formData.department_id}
                    onChange={(e) => setFormData({ ...formData, department_id: Number(e.target.value) })}
                    className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium"
                  >
                    <option value={1}>CSE - Computer Science</option>
                    <option value={2}>IT - Information Tech</option>
                    <option value={3}>DS - Data Science</option>
                    <option value={4}>EE - Electrical</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Current GPA</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.gpa}
                    onChange={(e) => setFormData({ ...formData, gpa: Number(e.target.value) })}
                    className="w-full bg-purple-50/40 border border-purple-100 p-2 rounded-xl text-slate-900 font-medium"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Study Hrs/Wk</label>
                  <input
                    type="number"
                    value={formData.study_hours}
                    onChange={(e) => setFormData({ ...formData, study_hours: Number(e.target.value) })}
                    className="w-full bg-purple-50/40 border border-purple-100 p-2 rounded-xl text-slate-900 font-medium"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Backlogs</label>
                  <input
                    type="number"
                    value={formData.backlogs}
                    onChange={(e) => setFormData({ ...formData, backlogs: Number(e.target.value) })}
                    className="w-full bg-purple-50/40 border border-purple-100 p-2 rounded-xl text-slate-900 font-medium"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold text-xs shadow-lg shadow-purple-500/20 mt-4"
              >
                Save & Run Initial AI Prediction
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminStudents;
