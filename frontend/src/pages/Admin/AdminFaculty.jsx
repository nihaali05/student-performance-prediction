import React, { useEffect, useState } from 'react';
import { getFacultyList, createFaculty } from '../../services/api';
import { UserCheck, Plus, X, Phone, Mail, Building2 } from 'lucide-react';

const AdminFaculty = () => {
  const [faculty, setFaculty] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    employee_id: '',
    department_id: 1,
    phone: ''
  });

  const fetchFaculty = async () => {
    setLoading(true);
    try {
      const res = await getFacultyList();
      setFaculty(res.data.faculty);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFaculty();
  }, []);

  const handleCreateFaculty = async (e) => {
    e.preventDefault();
    try {
      await createFaculty(formData);
      setShowModal(false);
      fetchFaculty();
    } catch (err) {
      alert(err.response?.data?.message || 'Error creating faculty.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Faculty & Educator Directory</h1>
          <p className="text-xs text-purple-700 font-medium mt-1">Manage teaching staff, department assignments, and access credentials.</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-purple-500/20 transition-all self-start"
        >
          <Plus className="w-4 h-4" />
          <span>Add Faculty Member</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {loading ? (
          <div className="col-span-full p-8 text-center text-slate-500 text-xs font-medium">Loading faculty profiles...</div>
        ) : faculty.map((f) => (
          <div key={f.id} className="glass-panel p-5 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-md shadow-purple-500/20">
                {f.name.charAt(0)}
              </div>
              <div>
                <h3 className="font-bold text-sm text-slate-900">{f.name}</h3>
                <span className="text-[11px] font-mono font-bold text-purple-700 bg-purple-100 px-2 py-0.5 rounded-lg border border-purple-200">
                  {f.employee_id}
                </span>
              </div>
            </div>

            <div className="space-y-2 text-xs text-slate-600 pt-2 border-t border-purple-100 font-medium">
              <div className="flex items-center gap-2">
                <Building2 className="w-3.5 h-3.5 text-purple-500" />
                <span>Department: <strong className="text-slate-900">{f.department_name}</strong></span>
              </div>
              <div className="flex items-center gap-2">
                <Mail className="w-3.5 h-3.5 text-purple-500" />
                <span className="truncate text-slate-800">{f.email}</span>
              </div>
              <div className="flex items-center gap-2">
                <Phone className="w-3.5 h-3.5 text-purple-500" />
                <span>{f.phone || 'N/A'}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white p-6 max-w-md w-full relative rounded-3xl border border-purple-100 shadow-2xl">
            <button onClick={() => setShowModal(false)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-800">
              <X className="w-5 h-5" />
            </button>
            <h3 className="text-lg font-extrabold text-slate-900 mb-4 flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-purple-600" />
              <span>Add Faculty Member</span>
            </h3>

            <form onSubmit={handleCreateFaculty} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 font-bold mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium"
                  placeholder="Prof. Jane Doe"
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
                  placeholder="jane.doe@analytics.edu"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Employee ID</label>
                  <input
                    type="text"
                    required
                    value={formData.employee_id}
                    onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                    className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium"
                    placeholder="EMP-CSE-005"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Department</label>
                  <select
                    value={formData.department_id}
                    onChange={(e) => setFormData({ ...formData, department_id: Number(e.target.value) })}
                    className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium"
                  >
                    <option value={1}>CSE</option>
                    <option value={2}>IT</option>
                    <option value={3}>DS</option>
                    <option value={4}>EE</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Phone Number</label>
                <input
                  type="text"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium"
                  placeholder="+1 555-0199"
                />
              </div>

              <button
                type="submit"
                className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold text-xs shadow-lg shadow-purple-500/20 mt-4"
              >
                Create Faculty Account
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminFaculty;
