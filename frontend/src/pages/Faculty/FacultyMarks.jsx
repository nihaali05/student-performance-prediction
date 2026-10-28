import React, { useEffect, useState } from 'react';
import { getMarks, addMark, getStudents, getSubjects } from '../../services/api';
import { FileSpreadsheet, Plus, X } from 'lucide-react';

const FacultyMarks = () => {
  const [marksList, setMarksList] = useState([]);
  const [students, setStudents] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [formError, setFormError] = useState('');

  const [formData, setFormData] = useState({
    student_id: null,
    subject_id: null,
    test_type: 'Unit Test 2',
    score: 78.0,
    max_score: 100.0,
    date: new Date().toISOString().split('T')[0]
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [mksRes, stuRes, subjectRes] = await Promise.all([
        getMarks(),
        getStudents(),
        getSubjects()
      ]);
      setMarksList(mksRes.data.marks);
      setStudents(stuRes.data.students);
      setSubjects(subjectRes.data.subjects);
      setLoadError('');
      if (stuRes.data.students.length > 0) {
        const firstStudent = stuRes.data.students[0];
        const studentSubjects = firstStudent.department_id == null
          ? subjectRes.data.subjects
          : subjectRes.data.subjects.filter((subject) => subject.department_id === firstStudent.department_id);
        setFormData((prev) => ({
          ...prev,
          student_id: firstStudent.id,
          subject_id: studentSubjects[0]?.id ?? null
        }));
      }
    } catch (err) {
      console.error(err);
      setLoadError('Could not load marks, students, or subjects. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.subject_id || !formData.student_id) {
      setFormError('Select both a student and a subject before saving.');
      return;
    }
    try {
      await addMark(formData);
      setShowModal(false);
      setFormError('');
      await fetchData();
    } catch (err) {
      setFormError(err.response?.data?.message || 'Failed to save mark entry.');
    }
  };

  const selectedStudent = students.find((student) => student.id === formData.student_id);
  const availableSubjects = selectedStudent?.department_id == null
    ? subjects
    : subjects.filter((subject) => subject.department_id === selectedStudent.department_id);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Internal Marks & Exam Entry</h1>
          <p className="text-xs text-purple-700 font-medium mt-1">Record midterms, unit tests, and quizzes. Updates trigger live performance re-evaluation.</p>
        </div>
        <button
          type="button"
          onClick={() => { setFormError(''); setShowModal(true); }}
          disabled={loading || Boolean(loadError) || students.length === 0 || subjects.length === 0}
          title={loadError || (!subjects.length ? 'No subjects are available.' : undefined)}
          className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-purple-500/20 transition-all self-start"
        >
          <Plus className="w-4 h-4" />
          <span>Enter Exam Score</span>
        </button>
      </div>

      {loadError && <div role="alert" className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium">{loadError}</div>}
      {!loading && !loadError && (students.length === 0 || subjects.length === 0) && (
        <div role="status" className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-medium">
          Mark entry is unavailable because {students.length === 0 ? 'no students' : 'no subjects'} are available.
        </div>
      )}

      <div className="glass-panel p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-purple-900 bg-purple-50/80 uppercase tracking-wider font-bold">
              <tr>
                <th className="p-3">Date</th>
                <th className="p-3">Student Name</th>
                <th className="p-3">Subject</th>
                <th className="p-3">Test Type</th>
                <th className="p-3">Score Obtd</th>
                <th className="p-3">Percentage</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-purple-100 text-slate-700 font-medium">
              {loading ? (
                <tr>
                  <td colSpan="6" className="p-6 text-center text-slate-500">Loading exam marks...</td>
                </tr>
              ) : (
                marksList.map((m) => (
                  <tr key={m.id} className="hover:bg-purple-50/40">
                    <td className="p-3 font-mono text-slate-500">{m.date}</td>
                    <td className="p-3 font-bold text-slate-900">{m.student_name}</td>
                    <td className="p-3">{m.subject_code} - {m.subject_name}</td>
                    <td className="p-3 font-bold text-purple-700">{m.test_type}</td>
                    <td className="p-3 font-extrabold text-slate-900">{m.score} / {m.max_score}</td>
                    <td className="p-3 font-bold text-emerald-600">{((m.score / m.max_score) * 100).toFixed(1)}%</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white p-6 max-w-md w-full relative rounded-3xl border border-purple-100 shadow-2xl">
            <button onClick={() => setShowModal(false)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-800">
              <X className="w-5 h-5" />
            </button>
            <h3 className="text-lg font-extrabold text-slate-900 mb-4 flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-purple-600" />
              <span>Record Exam Mark</span>
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 font-bold mb-1">Select Student</label>
                <select
                  required
                  value={formData.student_id ?? ''}
                  onChange={(e) => {
                    const studentId = e.target.value ? Number(e.target.value) : null;
                    const student = students.find((item) => item.id === studentId);
                    const studentSubjects = student?.department_id == null
                      ? subjects
                      : subjects.filter((subject) => subject.department_id === student.department_id);
                    setFormData({
                      ...formData,
                      student_id: studentId,
                      subject_id: studentSubjects[0]?.id ?? null
                    });
                  }}
                  className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium"
                >
                  <option value="" disabled>Select a student</option>
                  {students.map((s) => (
                    <option key={s.id} value={s.id}>{s.name} ({s.student_code})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Select Subject</label>
                <select
                  required
                  value={formData.subject_id ?? ''}
                  onChange={(e) => setFormData({ ...formData, subject_id: e.target.value ? Number(e.target.value) : null })}
                  disabled={!availableSubjects.length}
                  className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium disabled:opacity-60"
                >
                  <option value="" disabled>
                    {availableSubjects.length ? 'Select a subject' : 'No subjects available for this student'}
                  </option>
                  {availableSubjects.map((subject) => (
                    <option key={subject.id} value={subject.id}>{subject.code} - {subject.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Test / Exam Type</label>
                <input
                  type="text"
                  required
                  value={formData.test_type}
                  onChange={(e) => setFormData({ ...formData, test_type: e.target.value })}
                  className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium"
                  placeholder="e.g. Midterm 1"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Score Obtained</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.score}
                    onChange={(e) => setFormData({ ...formData, score: Number(e.target.value) })}
                    className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Max Score</label>
                  <input
                    type="number"
                    value={formData.max_score}
                    onChange={(e) => setFormData({ ...formData, max_score: Number(e.target.value) })}
                    className="w-full bg-purple-50/40 border border-purple-100 p-2.5 rounded-xl text-slate-900 font-medium"
                  />
                </div>
              </div>

              {formError && <p role="alert" className="text-rose-700 font-medium">{formError}</p>}

              <button
                type="submit"
                disabled={!formData.student_id || !formData.subject_id || !availableSubjects.some((subject) => subject.id === formData.subject_id)}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-bold text-xs shadow-lg shadow-purple-500/20 mt-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Save Score & Trigger AI Model Re-predict
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default FacultyMarks;
