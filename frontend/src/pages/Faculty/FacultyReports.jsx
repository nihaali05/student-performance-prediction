import React, { useState } from 'react';
import { uploadDatasetCSV, downloadReport } from '../../services/api';
import { FileText, Download, Upload, CheckCircle2, AlertCircle, FileSpreadsheet } from 'lucide-react';

const FacultyReports = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [downloading, setDownloading] = useState(null);
  const [downloadError, setDownloadError] = useState('');

  const handleDownload = async (type, fallbackFilename) => {
    setDownloading(type);
    setDownloadError('');
    try {
      const response = await downloadReport(type);
      const disposition = response.headers['content-disposition'] || '';
      const encodedFilename = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1];
      const regularFilename = disposition.match(/filename="?([^";]+)"?/i)?.[1];
      let filename = regularFilename || fallbackFilename;
      if (encodedFilename) {
        try {
          filename = decodeURIComponent(encodedFilename);
        } catch {
          filename = fallbackFilename;
        }
      }
      const objectUrl = window.URL.createObjectURL(new Blob([response.data], { type: response.headers['content-type'] }));
      const link = document.createElement('a');
      link.href = objectUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => window.URL.revokeObjectURL(objectUrl), 1000);
    } catch {
      setDownloadError('Report download failed. Please try again.');
    } finally {
      setDownloading(null);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setUploadResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await uploadDatasetCSV(formData);
      setUploadResult({ success: true, message: res.data.message });
      setFile(null);
    } catch (err) {
      setUploadResult({ success: false, message: err.response?.data?.message || 'Upload failed.' });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Reports & Dataset Management</h1>
        <p className="text-xs text-purple-700 font-medium mt-1">Export downloadable academic reports (CSV) or bulk import CSV/Excel dataset files.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Download Reports Section */}
        <div className="glass-panel p-6 space-y-4">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Download className="w-5 h-5 text-purple-600" />
            <span>Download Analytical Reports</span>
          </h3>

          <div className="space-y-3 pt-2">
            {downloadError && (
              <div role="alert" className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium">
                {downloadError}
              </div>
            )}
            <button
              type="button"
              onClick={() => handleDownload('at_risk', 'at_risk_students_report.csv')}
              disabled={downloading !== null}
              className="p-4 rounded-xl bg-purple-50/40 hover:bg-purple-50 border border-purple-100 flex items-center justify-between text-xs font-semibold text-slate-800 transition-all group"
            >
              <div className="flex items-center gap-3">
                <FileText className="w-4 h-4 text-rose-600" />
                <div>
                  <p className="font-bold text-slate-900">At-Risk Student Priority Report</p>
                  <p className="text-[11px] text-slate-500 font-medium">CSV list of RED and ORANGE warning level students</p>
                </div>
              </div>
              <Download className="w-4 h-4 text-purple-400 group-hover:text-purple-700 transition-colors" />
            </button>

            <button
              type="button"
              onClick={() => handleDownload('student_performance', 'student_performance_summary.csv')}
              disabled={downloading !== null}
              className="p-4 rounded-xl bg-purple-50/40 hover:bg-purple-50 border border-purple-100 flex items-center justify-between text-xs font-semibold text-slate-800 transition-all group"
            >
              <div className="flex items-center gap-3">
                <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
                <div>
                  <p className="font-bold text-slate-900">Full Student Performance Summary</p>
                  <p className="text-[11px] text-slate-500 font-medium">Complete scores, attendance, study hours, and ML predictions</p>
                </div>
              </div>
              <Download className="w-4 h-4 text-purple-400 group-hover:text-purple-700 transition-colors" />
            </button>

            <button
              type="button"
              onClick={() => handleDownload('department', 'department_analytics_report.csv')}
              disabled={downloading !== null}
              className="p-4 rounded-xl bg-purple-50/40 hover:bg-purple-50 border border-purple-100 flex items-center justify-between text-xs font-semibold text-slate-800 transition-all group"
            >
              <div className="flex items-center gap-3">
                <FileText className="w-4 h-4 text-purple-600" />
                <div>
                  <p className="font-bold text-slate-900">Department Level Analytics Report</p>
                  <p className="text-[11px] text-slate-500 font-medium">Aggregated department means and risk counts</p>
                </div>
              </div>
              <Download className="w-4 h-4 text-purple-400 group-hover:text-purple-700 transition-colors" />
            </button>
          </div>
        </div>

        {/* Bulk Dataset CSV/Excel Upload Section */}
        <div className="glass-panel p-6 space-y-4">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Upload className="w-5 h-5 text-purple-600" />
            <span>Bulk Dataset CSV / Excel Importer</span>
          </h3>

          <p className="text-xs text-slate-600 font-medium">
            Upload CSV/Excel file containing columns: <code className="text-purple-700 font-bold">student_code, attendance, internal_marks, assignment_score, study_hours</code>.
            The pipeline will validate, store, run AI predictions, and trigger risk alerts.
          </p>

          <form onSubmit={handleUpload} className="space-y-4 pt-2">
            <div className="border-2 border-dashed border-purple-200 hover:border-purple-400 rounded-2xl p-6 text-center transition-all bg-purple-50/30">
              <Upload className="w-8 h-8 text-purple-600 mx-auto mb-2" />
              <p className="text-xs text-slate-700 font-bold mb-1">
                {file ? file.name : 'Select or drag CSV / Excel file here'}
              </p>
              <input
                type="file"
                accept=".csv, .xlsx, .xls"
                onChange={handleFileChange}
                className="block w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-purple-100 file:text-purple-800 hover:file:bg-purple-200 cursor-pointer"
              />
            </div>

            {uploadResult && (
              <div className={`p-3.5 rounded-xl border text-xs flex items-center gap-2 font-medium ${
                uploadResult.success ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-rose-50 border-rose-200 text-rose-800'
              }`}>
                {uploadResult.success ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                <span>{uploadResult.message}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={!file || uploading}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold text-xs shadow-lg shadow-purple-500/20 transition-all disabled:opacity-50"
            >
              {uploading ? 'Processing Dataset & Running AI...' : 'Upload & Process Dataset'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default FacultyReports;
