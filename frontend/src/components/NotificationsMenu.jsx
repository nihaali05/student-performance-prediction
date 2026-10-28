import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Bell, BookOpen, Check, Mail, MessageSquare, Send, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  getNotificationContacts,
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  sendNotificationMessage
} from '../services/api';

const NotificationsMenu = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const menuRef = useRef(null);
  const seenIds = useRef(new Set());
  const initialLoad = useRef(true);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [toast, setToast] = useState(null);
  const [composing, setComposing] = useState(false);
  const [contacts, setContacts] = useState([]);
  const [recipientId, setRecipientId] = useState('');
  const [draft, setDraft] = useState('');
  const [loadingContacts, setLoadingContacts] = useState(false);
  const [sending, setSending] = useState(false);
  const [loadError, setLoadError] = useState('');
  const [error, setError] = useState('');
  const [feedback, setFeedback] = useState('');

  const refreshNotifications = useCallback(async (announceNew = false) => {
    try {
      const response = await getNotifications();
      const nextNotifications = response.data.notifications || [];

      if (initialLoad.current) {
        nextNotifications.forEach((item) => seenIds.current.add(item.id));
        initialLoad.current = false;
      } else {
        const incoming = nextNotifications.filter((item) => !seenIds.current.has(item.id));
        nextNotifications.forEach((item) => seenIds.current.add(item.id));
        if (announceNew && incoming.length > 0) setToast(incoming[0]);
      }

      setNotifications(nextNotifications);
      setUnreadCount(response.data.unread_count || 0);
      setLoadError('');
    } catch (requestError) {
      console.error('Could not load notifications:', requestError);
      setLoadError(requestError.response?.data?.message || 'Could not load notifications. Retrying…');
    }
  }, []);

  useEffect(() => {
    if (!user) return undefined;

    seenIds.current = new Set();
    initialLoad.current = true;
    refreshNotifications();
    const intervalId = window.setInterval(() => refreshNotifications(true), 10000);
    return () => window.clearInterval(intervalId);
  }, [user, refreshNotifications]);

  useEffect(() => {
    if (!toast) return undefined;
    const timeoutId = window.setTimeout(() => setToast(null), 7000);
    return () => window.clearTimeout(timeoutId);
  }, [toast]);

  useEffect(() => {
    const closeOnOutsideClick = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) setIsOpen(false);
    };
    document.addEventListener('mousedown', closeOnOutsideClick);
    return () => document.removeEventListener('mousedown', closeOnOutsideClick);
  }, []);

  const handleOpenComposer = async () => {
    setError('');
    setFeedback('');
    setComposing(true);
    setLoadingContacts(true);
    try {
      const response = await getNotificationContacts();
      const availableContacts = response.data.contacts || [];
      setContacts(availableContacts);
      setRecipientId((current) => current || String(availableContacts[0]?.id || ''));
    } catch (requestError) {
      setError(requestError.response?.data?.message || 'Could not load message recipients.');
    } finally {
      setLoadingContacts(false);
    }
  };

  const handleSendMessage = async (event) => {
    event.preventDefault();
    if (!recipientId || !draft.trim() || sending) return;

    setSending(true);
    setError('');
    setFeedback('');
    try {
      await sendNotificationMessage({
        recipient_user_id: Number(recipientId),
        message: draft.trim()
      });
      setDraft('');
      setComposing(false);
      setFeedback('Message sent.');
      refreshNotifications();
    } catch (requestError) {
      setError(requestError.response?.data?.message || 'Could not send your message.');
    } finally {
      setSending(false);
    }
  };

  const handleMarkRead = async (notification) => {
    if (!notification.is_read) {
      try {
        await markNotificationRead(notification.id);
        await refreshNotifications();
      } catch (requestError) {
        console.error('Could not mark notification as read:', requestError);
      }
    }
    if (notification.type === 'material' && user?.role === 'student') {
      navigate('/student/study-assistant');
      setIsOpen(false);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      await refreshNotifications();
    } catch (requestError) {
      setError(requestError.response?.data?.message || 'Could not mark notifications as read.');
    }
  };

  if (!user) return null;

  return (
    <>
      {toast && (
        <div className="fixed right-5 top-20 z-50 w-[min(24rem,calc(100vw-2.5rem))] rounded-2xl border border-purple-200 bg-white p-4 shadow-xl">
          <div className="flex items-start gap-3">
            <div className="rounded-xl bg-purple-100 p-2 text-purple-700">
              <Mail className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-bold text-purple-900">{toast.title}</p>
              <p className="mt-1 line-clamp-2 text-xs text-slate-600">{toast.message}</p>
              <button
                onClick={() => {
                  setIsOpen(true);
                  setToast(null);
                }}
                className="mt-2 text-xs font-bold text-purple-700 hover:text-purple-900"
              >
                View notification
              </button>
            </div>
            <button onClick={() => setToast(null)} aria-label="Dismiss notification" className="text-slate-400 hover:text-slate-700">
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      <div className="relative" ref={menuRef}>
        <button
          type="button"
          aria-label={`Notifications${unreadCount ? `, ${unreadCount} unread` : ''}`}
          aria-expanded={isOpen}
          onClick={() => {
            const nextOpen = !isOpen;
            setIsOpen(nextOpen);
            if (nextOpen) refreshNotifications();
          }}
          className="relative rounded-xl p-2 text-purple-600 transition-all hover:bg-purple-50 hover:text-purple-800"
        >
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -right-1 -top-1 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </button>

        {isOpen && (
          <section className="absolute right-0 top-12 z-40 w-[min(24rem,calc(100vw-2rem))] overflow-hidden rounded-2xl border border-purple-100 bg-white shadow-2xl">
            <div className="flex items-center justify-between border-b border-purple-100 px-4 py-3">
              <div>
                <h2 className="text-sm font-extrabold text-slate-900">Inbox</h2>
                <p className="text-[11px] text-slate-500">
                  {unreadCount ? `${unreadCount} unread` : 'You’re all caught up'}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {unreadCount > 0 && (
                  <button onClick={handleMarkAllRead} className="text-[11px] font-bold text-purple-700 hover:text-purple-900">
                    Mark all read
                  </button>
                )}
                {(user.role === 'student' || user.role === 'faculty') && (
                  <button
                    onClick={composing ? () => setComposing(false) : handleOpenComposer}
                    aria-label={composing ? 'Close message form' : 'Compose message'}
                    className="rounded-lg bg-purple-50 p-2 text-purple-700 hover:bg-purple-100"
                  >
                    {composing ? <X className="h-4 w-4" /> : <Send className="h-4 w-4" />}
                  </button>
                )}
              </div>
            </div>
            {loadError && <p role="alert" className="px-4 pt-3 text-xs font-medium text-rose-700">{loadError}</p>}

            {composing && (
              <form onSubmit={handleSendMessage} className="space-y-2 border-b border-purple-100 bg-purple-50/40 p-4">
                {loadingContacts ? (
                  <p className="text-xs text-slate-500">Loading contacts…</p>
                ) : contacts.length === 0 ? (
                  <p className="text-xs text-slate-600">There are no message recipients in your department.</p>
                ) : (
                  <>
                    <label htmlFor="notification-recipient" className="sr-only">Recipient</label>
                    <select
                      id="notification-recipient"
                      value={recipientId}
                      onChange={(event) => setRecipientId(event.target.value)}
                      className="w-full rounded-xl border border-purple-200 bg-white px-3 py-2 text-xs text-slate-800 outline-none focus:border-purple-500"
                    >
                      {contacts.map((contact) => (
                        <option key={contact.id} value={contact.id}>
                          {contact.name} · {contact.role}
                        </option>
                      ))}
                    </select>
                    <label htmlFor="notification-message" className="sr-only">Message</label>
                    <textarea
                      id="notification-message"
                      rows="3"
                      maxLength="5000"
                      required
                      value={draft}
                      onChange={(event) => setDraft(event.target.value)}
                      placeholder="Write a message…"
                      className="w-full resize-none rounded-xl border border-purple-200 bg-white px-3 py-2 text-xs text-slate-800 outline-none focus:border-purple-500"
                    />
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        disabled={sending || !recipientId || !draft.trim()}
                        className="flex items-center gap-1.5 rounded-lg bg-purple-700 px-3 py-2 text-xs font-bold text-white hover:bg-purple-800 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <Send className="h-3.5 w-3.5" />
                        {sending ? 'Sending…' : 'Send message'}
                      </button>
                    </div>
                  </>
                )}
                {error && <p role="alert" className="text-xs font-medium text-rose-700">{error}</p>}
              </form>
            )}

            {feedback && <p role="status" className="px-4 pt-3 text-xs font-semibold text-emerald-700">{feedback}</p>}
            {!composing && error && <p role="alert" className="px-4 pt-3 text-xs font-medium text-rose-700">{error}</p>}

            <div className="max-h-[65vh] overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="px-6 py-10 text-center">
                  <MessageSquare className="mx-auto h-7 w-7 text-purple-300" />
                  <p className="mt-2 text-xs font-semibold text-slate-600">No notifications yet</p>
                  <p className="mt-1 text-[11px] text-slate-400">Messages and study updates will appear here.</p>
                </div>
              ) : notifications.map((notification) => (
                <button
                  type="button"
                  key={notification.id}
                  onClick={() => handleMarkRead(notification)}
                  className={`flex w-full items-start gap-3 border-b border-slate-100 px-4 py-3 text-left transition-colors hover:bg-purple-50/60 ${
                    notification.is_read ? 'bg-white' : 'bg-purple-50/40'
                  }`}
                >
                  <span className={`mt-0.5 rounded-lg p-2 ${
                    notification.type === 'material' ? 'bg-emerald-50 text-emerald-700' : 'bg-purple-100 text-purple-700'
                  }`}>
                    {notification.type === 'material' ? <BookOpen className="h-4 w-4" /> : <MessageSquare className="h-4 w-4" />}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-center justify-between gap-2">
                      <span className="truncate text-xs font-bold text-slate-900">{notification.title}</span>
                      {!notification.is_read && <span className="h-2 w-2 shrink-0 rounded-full bg-purple-600" />}
                    </span>
                    <span className="mt-1 block whitespace-pre-wrap break-words text-xs text-slate-600">{notification.message}</span>
                    <span className="mt-1.5 block text-[10px] text-slate-400">
                      {new Date(notification.created_at).toLocaleString()}
                    </span>
                  </span>
                  {notification.is_read && <Check className="mt-1 h-3.5 w-3.5 shrink-0 text-emerald-600" />}
                </button>
              ))}
            </div>
          </section>
        )}
      </div>
    </>
  );
};

export default NotificationsMenu;
