import React, { useCallback, useState, useEffect } from 'react';
import {
  FileText, Upload, Sparkles, MessageSquare, History,
  AlertTriangle, CheckCircle, Eye, Trash2,
  BookOpen, Layers, Award, RefreshCw, Send, Check, X
} from 'lucide-react';
import {
  uploadStudyMaterial, getStudyMaterials, getStudyMaterialDetail, deleteStudyMaterial,
  sendStudyChatQuestion, generateStudyQuiz, submitStudyQuiz, getQuizHistory
} from '../../services/api';

const StudentStudyAssistant = () => {
  const [activeTab, setActiveTab] = useState('materials'); // 'materials', 'chat', 'quiz', 'history'
  
  // Materials state
  const [materials, setMaterials] = useState([]);
  const [loadingMaterials, setLoadingMaterials] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  
  // Debug preview state
  const [previewMaterial, setPreviewMaterial] = useState(null);
  const [showDebugModal, setShowDebugModal] = useState(false);
  
  // Chat state
  const [selectedMaterialId, setSelectedMaterialId] = useState('');
  const [chatMessages, setChatMessages] = useState([
    {
      sender: 'assistant',
      text: 'Hi! Ask me about any subject, get help understanding a topic, or ask a follow-up question. I can also use relevant excerpts from your uploaded study materials.',
      sources: []
    }
  ]);
  const [questionInput, setQuestionInput] = useState('');
  const [askingChat, setAskingChat] = useState(false);
  
  // Quiz Generator state
  const [quizMaterialId, setQuizMaterialId] = useState('');
  const [questionCount, setQuestionCount] = useState(5);
  const [difficulty, setDifficulty] = useState('Medium');
  const [generatingQuiz, setGeneratingQuiz] = useState(false);
  const [activeQuiz, setActiveQuiz] = useState(null);
  const [userAnswers, setUserAnswers] = useState({});
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [quizResult, setQuizResult] = useState(null);
  const [submittingQuiz, setSubmittingQuiz] = useState(false);
  
  // History state
  const [historyList, setHistoryList] = useState([]);
  const [weakTopics, setWeakTopics] = useState([]);

  const fetchMaterials = useCallback(async (showLoading = true) => {
    if (showLoading) setLoadingMaterials(true);
    try {
      const res = await getStudyMaterials();
      const fetched = res.data.materials || [];
      setMaterials(fetched);
      setSelectedMaterialId((prev) => {
        if (!prev) return '';
        return fetched.some((m) => String(m.id) === String(prev)) ? prev : '';
      });
    } catch (err) {
      console.error('Error fetching materials:', err);
    } finally {
      setLoadingMaterials(false);
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      const res = await getQuizHistory();
      setHistoryList(res.data.history || []);
      setWeakTopics(res.data.weakTopicsSummary || []);
    } catch (err) {
      console.error('Error fetching history:', err);
    }
  }, []);

  useEffect(() => {
    fetchMaterials(false);
    fetchHistory();
  }, [fetchMaterials, fetchHistory]);

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    setUploadMessage(null);
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await uploadStudyMaterial(formData);
      setUploadMessage(res.data.message || 'File uploaded successfully!');
      setSelectedFile(null);
      // Reset file input element
      const el = document.getElementById('study-file-input');
      if (el) el.value = '';
      fetchMaterials();
    } catch (err) {
      const msg = err.response?.data?.message || 'Failed to extract text from document. Please ensure it is a valid PDF or image.';
      setUploadError(msg);
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteMaterial = async (id) => {
    if (!window.confirm('Are you sure you want to delete this study material?')) return;
    try {
      await deleteStudyMaterial(id);
      fetchMaterials();
    } catch (err) {
      alert(err.response?.data?.message || 'Failed to delete material.');
    }
  };

  const handleOpenDebugPreview = async (mat) => {
    try {
      const res = await getStudyMaterialDetail(mat.id);
      setPreviewMaterial(res.data.material);
      setShowDebugModal(true);
    } catch (err) {
      alert(err.response?.data?.message || 'Could not fetch preview content.');
    }
  };

  const handleSendQuestion = async (e) => {
    e.preventDefault();
    if (!questionInput.trim() || askingChat) return;

    const userQ = questionInput.trim();
    setQuestionInput('');
    setChatMessages((prev) => [...prev, { sender: 'user', text: userQ }]);
    setAskingChat(true);

    try {
      const res = await sendStudyChatQuestion({
        question: userQ,
        study_material_id: selectedMaterialId ? parseInt(selectedMaterialId) : null,
        history: chatMessages.slice(1).slice(-20).map((message) => ({
          role: message.sender,
          content: message.text
        }))
      });

      setChatMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: res.data.answer,
          sources: res.data.sources || []
        }
      ]);
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: err.response?.data?.message || 'Sorry, I could not get a response. Please try again.',
          sources: []
        }
      ]);
    } finally {
      setAskingChat(false);
    }
  };

  const handleGenerateQuiz = async (e) => {
    e.preventDefault();
    setGeneratingQuiz(true);
    setActiveQuiz(null);
    setQuizResult(null);
    setUserAnswers({});
    setQuizSubmitted(false);

    try {
      const res = await generateStudyQuiz({
        study_material_id: quizMaterialId ? parseInt(quizMaterialId) : null,
        question_count: parseInt(questionCount),
        difficulty: difficulty
      });

      setActiveQuiz(res.data);
    } catch (err) {
      alert(err.response?.data?.message || 'Failed to generate quiz from study material.');
    } finally {
      setGeneratingQuiz(false);
    }
  };

  const handleSelectAnswer = (qIndex, optionVal) => {
    setUserAnswers((prev) => ({
      ...prev,
      [qIndex]: optionVal
    }));
  };

  const handleSubmitQuiz = async () => {
    if (!activeQuiz) return;
    setSubmittingQuiz(true);

    try {
      const res = await submitStudyQuiz({
        quiz_id: activeQuiz.quizId,
        study_material_id: quizMaterialId ? parseInt(quizMaterialId) : null,
        questions: activeQuiz.questions,
        answers: userAnswers
      });

      setQuizResult(res.data);
      setQuizSubmitted(true);
      fetchHistory();
    } catch (err) {
      alert(err.response?.data?.message || 'Error submitting quiz answers.');
    } finally {
      setSubmittingQuiz(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header Banner */}
      <div className="bg-gradient-to-r from-purple-700 via-indigo-700 to-purple-900 rounded-2xl p-6 text-white shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-white/20 text-purple-100 backdrop-blur-md">
              General AI Chat
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-400/20 text-emerald-200 backdrop-blur-md">
              Study Material Support
            </span>
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight">AI Study Assistant & Quiz Generator</h1>
          <p className="text-purple-200 text-sm mt-1 max-w-2xl">
            Upload PDF & Image study materials. Our vision and extraction pipeline reads the actual document text to generate verified quizzes and answer questions.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab('materials')}
            className="px-4 py-2.5 rounded-xl bg-white text-purple-800 font-semibold text-sm hover:bg-purple-50 transition shadow-sm flex items-center gap-2"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Document</span>
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 overflow-x-auto bg-white rounded-xl shadow-sm p-1.5 gap-1">
        <button
          onClick={() => setActiveTab('materials')}
          className={`px-4 py-2.5 rounded-lg text-sm font-medium transition flex items-center gap-2 ${
            activeTab === 'materials'
              ? 'bg-purple-600 text-white shadow-sm'
              : 'text-slate-600 hover:text-purple-700 hover:bg-purple-50'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          <span>Study Materials ({materials.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('chat')}
          className={`px-4 py-2.5 rounded-lg text-sm font-medium transition flex items-center gap-2 ${
            activeTab === 'chat'
              ? 'bg-purple-600 text-white shadow-sm'
              : 'text-slate-600 hover:text-purple-700 hover:bg-purple-50'
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          <span>          Ask AI Assistant</span>
        </button>

        <button
          onClick={() => setActiveTab('quiz')}
          className={`px-4 py-2.5 rounded-lg text-sm font-medium transition flex items-center gap-2 ${
            activeTab === 'quiz'
              ? 'bg-purple-600 text-white shadow-sm'
              : 'text-slate-600 hover:text-purple-700 hover:bg-purple-50'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>AI Quiz Generator</span>
        </button>

        <button
          onClick={() => setActiveTab('history')}
          className={`px-4 py-2.5 rounded-lg text-sm font-medium transition flex items-center gap-2 ${
            activeTab === 'history'
              ? 'bg-purple-600 text-white shadow-sm'
              : 'text-slate-600 hover:text-purple-700 hover:bg-purple-50'
          }`}
        >
          <History className="w-4 h-4" />
          <span>Quiz History & Weak Topics</span>
        </button>
      </div>

      {/* TAB 1: STUDY MATERIALS & UPLOAD */}
      {activeTab === 'materials' && (
        <div className="space-y-6">
          {/* Upload Card */}
          <div className="bg-white rounded-2xl p-6 border border-purple-100 shadow-sm">
            <h2 className="text-base font-bold text-slate-900 mb-1 flex items-center gap-2">
              <Upload className="w-5 h-5 text-purple-600" />
              Upload New Study Material
            </h2>
            <p className="text-xs text-slate-500 mb-4">
              Supported formats: <strong>PDF, PNG, JPG, JPEG</strong> (Max 16 MB). Content is extracted per-page for document-grounded AI.
            </p>

            <form onSubmit={handleFileUpload} className="space-y-4">
              <div className="border-2 border-dashed border-purple-200 rounded-xl p-6 text-center hover:border-purple-400 transition bg-purple-50/30">
                <input
                  id="study-file-input"
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={(e) => setSelectedFile(e.target.files[0] || null)}
                  className="hidden"
                />
                <label htmlFor="study-file-input" className="cursor-pointer flex flex-col items-center gap-2">
                  <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center text-purple-600">
                    <FileText className="w-6 h-6" />
                  </div>
                  <span className="text-sm font-semibold text-purple-900">
                    {selectedFile ? selectedFile.name : 'Click to browse or drop file here'}
                  </span>
                  <span className="text-xs text-slate-400">PDF, PNG, JPG, JPEG supported</span>
                </label>
              </div>

              {uploadError && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>{uploadError}</span>
                </div>
              )}

              {uploadMessage && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs rounded-xl flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 shrink-0" />
                  <span>{uploadMessage}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={!selectedFile || uploading}
                className="w-full py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-semibold text-sm transition shadow-md disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Processing & Extracting Content...</span>
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    <span>Upload & Process Document</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Uploaded Materials List */}
          <div className="bg-white rounded-2xl p-6 border border-purple-100 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Layers className="w-5 h-5 text-purple-600" />
                Uploaded Study Materials
              </h2>
              <button
                onClick={fetchMaterials}
                className="p-2 text-slate-500 hover:text-purple-600 rounded-lg hover:bg-purple-50"
                title="Refresh List"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>

            {loadingMaterials ? (
              <div className="text-center py-8 text-slate-400 text-sm">Loading materials...</div>
            ) : materials.length === 0 ? (
              <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-xl">
                <BookOpen className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="text-sm text-slate-500 font-medium">No study materials uploaded yet.</p>
                <p className="text-xs text-slate-400 mt-1">You can chat without a document. Upload a PDF or image to get document-based answers and generate quizzes.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {materials.map((mat) => (
                  <div key={mat.id} className="p-4 border border-purple-100 rounded-xl bg-purple-50/20 hover:shadow-md transition space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <FileText className="w-5 h-5 text-purple-600 shrink-0" />
                        <span className="font-bold text-sm text-slate-900 truncate" title={mat.originalFileName}>
                          {mat.originalFileName}
                        </span>
                      </div>
                      <span className={`px-2 py-0.5 rounded-md text-[11px] font-bold uppercase tracking-wider ${
                        mat.extractionStatus === 'SUCCESS' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                      }`}>
                        {mat.extractionStatus}
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-xs text-slate-500 bg-white p-2 rounded-lg border border-purple-50">
                      <div>
                        <span className="block text-[10px] text-slate-400">Pages</span>
                        <span className="font-semibold text-slate-700">{mat.pageCount}</span>
                      </div>
                      <div>
                        <span className="block text-[10px] text-slate-400">Characters</span>
                        <span className="font-semibold text-slate-700">{mat.characterCount}</span>
                      </div>
                      <div>
                        <span className="block text-[10px] text-slate-400">Uploaded</span>
                        <span className="font-semibold text-slate-700">{mat.createdAt ? mat.createdAt.substring(0, 10) : 'Today'}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 pt-1 border-t border-purple-50">
                      <button
                        onClick={() => {
                          setSelectedMaterialId(mat.id);
                          setActiveTab('chat');
                        }}
                        className="flex-1 py-1.5 bg-purple-50 hover:bg-purple-100 text-purple-700 font-semibold text-xs rounded-lg transition flex items-center justify-center gap-1"
                      >
                        <MessageSquare className="w-3.5 h-3.5" />
                        <span>Open Chat</span>
                      </button>

                      <button
                        onClick={() => {
                          setQuizMaterialId(mat.id);
                          setActiveTab('quiz');
                        }}
                        className="flex-1 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs rounded-lg transition flex items-center justify-center gap-1"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Generate Quiz</span>
                      </button>

                      <button
                        onClick={() => handleOpenDebugPreview(mat)}
                        className="p-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition"
                        title="Development Debug Preview"
                      >
                        <Eye className="w-4 h-4" />
                      </button>

                      <button
                        onClick={() => handleDeleteMaterial(mat.id)}
                        className="p-1.5 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg transition"
                        title="Delete Material"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: AI STUDY CHATBOT */}
      {activeTab === 'chat' && (
        <div className="bg-white rounded-2xl border border-purple-100 shadow-sm flex flex-col h-[600px]">
          {/* Header */}
          <div className="p-4 border-b border-purple-100 flex items-center justify-between bg-purple-50/50 rounded-t-2xl">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-purple-600 flex items-center justify-center text-white">
                <MessageSquare className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-slate-900">AI Study Assistant</h3>
                <p className="text-[11px] text-purple-700 font-medium">Ask general questions or get help from your study materials</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-xs text-slate-500 font-medium">Study context:</label>
              <select
                value={selectedMaterialId}
                onChange={(e) => setSelectedMaterialId(e.target.value)}
                className="text-xs bg-white border border-purple-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-purple-500 font-medium text-slate-700"
              >
                <option value="">All my &amp; department materials</option>
                {materials.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.originalFileName}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Messages Window */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4">
            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl p-4 text-sm leading-relaxed ${
                    msg.sender === 'user'
                      ? 'bg-purple-600 text-white rounded-br-none shadow-md'
                      : 'bg-slate-100 text-slate-800 border border-slate-200/60 rounded-bl-none'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.text}</p>
                </div>

                {/* Sources List */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-1.5 flex items-center gap-1.5 text-xs text-purple-700 bg-purple-50 px-2.5 py-1 rounded-full border border-purple-200">
                    <span className="font-bold">Sources:</span>
                    {msg.sources.map((s, sIdx) => (
                      <span key={sIdx} className="bg-white px-2 py-0.5 rounded text-[11px] font-semibold text-purple-800 shadow-2xs border border-purple-100">
                        Page {s.page}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {askingChat && (
              <div className="flex items-center gap-2 text-xs text-purple-600 font-medium bg-purple-50 px-3 py-2 rounded-xl w-fit">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Thinking...</span>
              </div>
            )}
          </div>

          {/* Input Box */}
          <form onSubmit={handleSendQuestion} className="p-3 border-t border-purple-100 flex items-center gap-2">
            <input
              type="text"
              value={questionInput}
              onChange={(e) => setQuestionInput(e.target.value)}
              placeholder="Ask anything, or ask about your study materials..."
              className="flex-1 text-sm bg-slate-50 border border-purple-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <button
              type="submit"
              disabled={!questionInput.trim() || askingChat}
              className="px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-semibold text-sm rounded-xl transition shadow-md disabled:opacity-50 flex items-center gap-1.5"
            >
              <Send className="w-4 h-4" />
              <span>Send</span>
            </button>
          </form>
        </div>
      )}

      {/* TAB 3: AI QUIZ GENERATOR */}
      {activeTab === 'quiz' && (
        <div className="space-y-6">
          {/* Controls Card */}
          <div className="bg-white rounded-2xl p-6 border border-purple-100 shadow-sm">
            <h2 className="text-base font-bold text-slate-900 mb-1 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-600" />
              Generate Exam Practice MCQs
            </h2>
            <p className="text-xs text-slate-500 mb-4">
              Practice with multiple-choice exam questions grounded in your document. Each question has four choices and one correct answer.
            </p>

            <form onSubmit={handleGenerateQuiz} className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Study Material</label>
                <select
                  value={quizMaterialId}
                  onChange={(e) => setQuizMaterialId(e.target.value)}
                  className="w-full text-xs bg-slate-50 border border-purple-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="">All Uploaded Documents</option>
                  {materials.map((m) => (
                    <option key={m.id} value={m.id}>{m.originalFileName}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Question Count</label>
                <select
                  value={questionCount}
                  onChange={(e) => setQuestionCount(e.target.value)}
                  className="w-full text-xs bg-slate-50 border border-purple-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value={5}>5 Questions</option>
                  <option value={10}>10 Questions</option>
                  <option value={15}>15 Questions</option>
                  <option value={20}>20 Questions</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Difficulty</label>
                <select
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value)}
                  className="w-full text-xs bg-slate-50 border border-purple-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="Easy">Easy</option>
                  <option value="Medium">Medium</option>
                  <option value="Hard">Hard</option>
                </select>
              </div>

              <div className="flex items-end">
                <button
                  type="submit"
                  disabled={generatingQuiz || materials.length === 0}
                  className="w-full py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-semibold text-xs rounded-xl shadow-md transition disabled:opacity-50 flex items-center justify-center gap-1.5"
                >
                  {generatingQuiz ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Generating...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Generate Quiz</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Active Quiz Player */}
          {activeQuiz && !quizSubmitted && (
            <div className="bg-white rounded-2xl p-6 border border-purple-100 shadow-sm space-y-6">
              <div className="flex items-center justify-between border-b border-purple-100 pb-4">
                <div>
                  <h3 className="font-bold text-base text-slate-900">{activeQuiz.title}</h3>
                  <span className="text-xs text-purple-600 font-medium">Difficulty: {activeQuiz.difficulty} • Total: {activeQuiz.total} Questions</span>
                </div>
                <span className="px-3 py-1 bg-purple-100 text-purple-700 font-bold text-xs rounded-full">
                  Grounded Evaluation
                </span>
              </div>

              <div className="space-y-6">
                {activeQuiz.questions.map((q, qIdx) => (
                  <div key={qIdx} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
                    <div className="flex items-start gap-3">
                      <span className="w-6 h-6 rounded-full bg-purple-600 text-white font-bold text-xs flex items-center justify-center shrink-0">
                        {qIdx + 1}
                      </span>
                      <div className="flex-1">
                        <p className="font-bold text-sm text-slate-900">{q.question}</p>
                        <span className="text-[11px] text-purple-700 font-semibold">Source: Page {q.sourcePage}</span>
                      </div>
                    </div>

                    {/* Options list */}
                    <div className="space-y-2 pl-9">
                      {q.options && q.options.length > 0 ? (
                        q.options.map((opt, oIdx) => (
                          <label
                            key={oIdx}
                            className={`flex items-center gap-3 p-3 rounded-xl border text-xs cursor-pointer transition ${
                              userAnswers[qIdx] === opt
                                ? 'bg-purple-100 border-purple-400 font-bold text-purple-900'
                                : 'bg-white border-slate-200 hover:bg-purple-50/50 text-slate-700'
                            }`}
                          >
                            <input
                              type="radio"
                              name={`question-${qIdx}`}
                              value={opt}
                              checked={userAnswers[qIdx] === opt}
                              onChange={() => handleSelectAnswer(qIdx, opt)}
                              className="text-purple-600 focus:ring-purple-500"
                            />
                            <span>{opt}</span>
                          </label>
                        ))
                      ) : (
                        <input
                          type="text"
                          value={userAnswers[qIdx] || ''}
                          onChange={(e) => handleSelectAnswer(qIdx, e.target.value)}
                          placeholder="Type your answer based on document text..."
                          className="w-full text-xs bg-white border border-slate-300 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                      )}
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex justify-end pt-4 border-t border-purple-100">
                <button
                  onClick={handleSubmitQuiz}
                  disabled={submittingQuiz}
                  className="px-6 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold text-sm rounded-xl shadow-lg transition disabled:opacity-50 flex items-center gap-2"
                >
                  {submittingQuiz ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Evaluating Answers...</span>
                    </>
                  ) : (
                    <>
                      <Check className="w-4 h-4" />
                      <span>Submit Quiz</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Quiz Results Card */}
          {quizSubmitted && quizResult && (
            <div className="bg-white rounded-2xl p-6 border border-purple-100 shadow-sm space-y-6">
              <div className="p-6 bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-100 rounded-2xl text-center space-y-2">
                <Award className="w-10 h-10 text-purple-600 mx-auto" />
                <h3 className="text-xl font-extrabold text-purple-950">Quiz Submission Results</h3>
                <div className="flex items-center justify-center gap-6 pt-2">
                  <div>
                    <span className="block text-2xl font-black text-purple-700">{quizResult.percentage}%</span>
                    <span className="text-xs text-slate-500 font-medium">Score Percentage</span>
                  </div>
                  <div>
                    <span className="block text-2xl font-black text-emerald-600">{quizResult.correctCount} / {quizResult.totalQuestions}</span>
                    <span className="text-xs text-slate-500 font-medium">Correct Answers</span>
                  </div>
                </div>
              </div>

              {/* Detailed Questions Breakdown */}
              <div className="space-y-4">
                <h4 className="font-bold text-sm text-slate-900">Detailed Answer Explanation</h4>
                {quizResult.details && quizResult.details.map((d, dIdx) => (
                  <div key={dIdx} className={`p-4 rounded-xl border text-xs space-y-2 ${
                    d.isCorrect ? 'bg-emerald-50/40 border-emerald-200' : 'bg-red-50/40 border-red-200'
                  }`}>
                    <div className="flex items-start justify-between gap-2">
                      <p className="font-bold text-slate-900">{dIdx + 1}. {d.question}</p>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        d.isCorrect ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {d.isCorrect ? 'CORRECT' : 'WRONG'}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-slate-600 bg-white p-2 rounded-lg border border-slate-100">
                      <div>Your Answer: <strong className={d.isCorrect ? 'text-emerald-700' : 'text-red-700'}>{d.userAnswer}</strong></div>
                      <div>Correct Answer: <strong className="text-slate-900">{d.correctAnswer}</strong></div>
                    </div>

                    <p className="text-slate-600 italic">Explanation: {d.explanation}</p>
                    <span className="inline-block text-[10px] font-bold text-purple-700 bg-purple-100 px-2 py-0.5 rounded">
                      Source: Page {d.sourcePage}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: QUIZ HISTORY & WEAK TOPICS */}
      {activeTab === 'history' && (
        <div className="space-y-6">
          {/* Weak Topics Summary Card */}
          <div className="bg-white rounded-2xl p-6 border border-purple-100 shadow-sm">
            <h2 className="text-base font-bold text-slate-900 mb-2 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              Identified Weak Topics
            </h2>
            <p className="text-xs text-slate-500 mb-4">
              Topics where performance was below threshold based on evaluated quiz submissions.
            </p>

            {weakTopics.length === 0 ? (
              <p className="text-xs text-emerald-600 font-semibold bg-emerald-50 p-3 rounded-xl border border-emerald-200">
                No weak topics identified yet. Complete quizzes to generate performance analytics.
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {weakTopics.map((wt, wIdx) => (
                  <span key={wIdx} className="px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200 flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                    <span>{wt}</span>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* History List */}
          <div className="bg-white rounded-2xl p-6 border border-purple-100 shadow-sm">
            <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
              <History className="w-5 h-5 text-purple-600" />
              Past Quiz Attempts
            </h2>

            {historyList.length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">No past quiz attempts found.</p>
            ) : (
              <div className="space-y-3">
                {historyList.map((h) => (
                  <div key={h.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 flex items-center justify-between text-xs">
                    <div>
                      <span className="font-bold text-slate-900 text-sm">Attempt #{h.id}</span>
                      <span className="block text-slate-400 text-[11px]">{h.submittedAt ? h.submittedAt.substring(0, 10) : ''}</span>
                    </div>
                    <div className="text-right">
                      <span className="font-extrabold text-sm text-purple-700">{h.percentage}%</span>
                      <span className="block text-slate-500 font-medium">{h.score} / {h.totalQuestions} correct</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Development Debug Preview Modal (Requirement 21) */}
      {showDebugModal && previewMaterial && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl border border-purple-200">
            <div className="p-4 border-b border-purple-100 flex items-center justify-between bg-purple-50 rounded-t-2xl">
              <div>
                <h3 className="font-bold text-sm text-purple-950 flex items-center gap-2">
                  <Eye className="w-4 h-4 text-purple-600" />
                  Development Extraction Preview (Debug Mode)
                </h3>
                <p className="text-xs text-purple-700 font-medium">Verify exact extracted text content stored in AI context</p>
              </div>
              <button
                onClick={() => setShowDebugModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-purple-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4 text-xs">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-purple-50/50 p-3 rounded-xl border border-purple-100">
                <div>
                  <span className="block text-[10px] text-slate-400">File Name</span>
                  <span className="font-bold text-slate-800 truncate block">{previewMaterial.originalFileName}</span>
                </div>
                <div>
                  <span className="block text-[10px] text-slate-400">Extraction Status</span>
                  <span className="font-bold text-emerald-700">{previewMaterial.extractionStatus}</span>
                </div>
                <div>
                  <span className="block text-[10px] text-slate-400">Total Pages</span>
                  <span className="font-bold text-slate-800">{previewMaterial.pageCount}</span>
                </div>
                <div>
                  <span className="block text-[10px] text-slate-400">Total Characters</span>
                  <span className="font-bold text-slate-800">{previewMaterial.characterCount}</span>
                </div>
              </div>

              <div>
                <h4 className="font-bold text-xs text-slate-800 mb-2">First 1,000 Extracted Characters:</h4>
                <div className="p-4 rounded-xl bg-slate-900 text-emerald-400 font-mono text-[11px] leading-relaxed overflow-x-auto whitespace-pre-wrap border border-slate-800 shadow-inner">
                  {previewMaterial.extractedTextPreview || 'No text extracted.'}
                </div>
              </div>
            </div>

            <div className="p-4 border-t border-purple-100 flex justify-end">
              <button
                onClick={() => setShowDebugModal(false)}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-semibold text-xs rounded-xl transition"
              >
                Close Debug Window
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentStudyAssistant;
