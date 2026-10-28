import axios from 'axios';

// In production, set VITE_API_BASE_URL to your deployed backend (e.g. https://edupredict-backend.onrender.com/api)
// In dev, Vite proxy forwards '/api' to localhost:5000 automatically.
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

const API = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT Token
API.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle unauth
API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default API;

// API functions
export const loginUser = (email, password) => API.post('/auth/login', { email, password });
export const getCurrentUser = () => API.get('/auth/me');

export const getStudents = (params) => API.get('/students', { params });
export const getStudentDetail = (id) => API.get(`/students/${id}`);
export const createStudent = (data) => API.post('/students', data);
export const getSubjects = () => API.get('/subjects');

export const getFacultyList = () => API.get('/faculty');
export const getFacultyDashboard = () => API.get('/faculty/dashboard');
export const createFaculty = (data) => API.post('/faculty', data);

export const getAttendance = (params) => API.get('/attendance', { params });
export const addAttendance = (data) => API.post('/attendance', data);

export const getMarks = (params) => API.get('/marks', { params });
export const addMark = (data) => API.post('/marks', data);

export const runBatchPredictions = () => API.post('/predictions/run');
export const runWhatIfSimulation = (data) => API.post('/predictions/what-if', data);

export const getWarnings = (params) => API.get('/warnings', { params });
export const resolveWarning = (id) => API.post(`/warnings/${id}/resolve`);

export const getInterventions = (params) => API.get('/interventions', { params });
export const createIntervention = (data) => API.post('/interventions', data);

export const uploadDatasetCSV = (formData) => API.post('/upload/csv', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});

export const getAdminAnalytics = () => API.get('/analytics/admin');
export const getModelStatus = () => API.get('/model/status');
export const retrainMLModels = () => API.post('/model/retrain');

export const downloadReport = (type, format = 'csv') => API.get('/reports/download', {
  params: { type, format },
  responseType: 'blob',
});

// Grounded AI Study Assistant & Quiz API
export const uploadStudyMaterial = (formData) => API.post('/study/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});
export const getStudyMaterials = () => API.get('/study/materials');
export const getStudyMaterialDetail = (id) => API.get(`/study/materials/${id}`);
export const deleteStudyMaterial = (id) => API.delete(`/study/materials/${id}`);

export const sendStudyChatQuestion = (data) => API.post('/study/chat', data);
export const generateStudyQuiz = (data) => API.post('/study/quiz/generate', data);
export const submitStudyQuiz = (data) => API.post('/study/quiz/submit', data);
export const getQuizHistory = () => API.get('/study/quiz/history');

export const getNotifications = () => API.get('/notifications');
export const getNotificationContacts = () => API.get('/notifications/contacts');
export const sendNotificationMessage = (data) => API.post('/notifications/message', data);
export const markNotificationRead = (id) => API.post(`/notifications/${id}/read`);
export const markAllNotificationsRead = () => API.post('/notifications/read-all');
