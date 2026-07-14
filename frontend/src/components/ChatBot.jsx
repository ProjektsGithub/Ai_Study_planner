import { useState, useRef, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import apiClient from '../api/client';
import { useStudyPlan } from '../context/StudyPlanContext';

// ── Task-type badge helper ───────────────────────────────────────────────────
const TASK_LABELS = {
  lecture_review:    { label: 'Cours',    color: '#818cf8' },
  exercise_practice: { label: 'Exercice', color: '#fb923c' },
  exam_preparation:  { label: 'Examen',   color: '#f87171' },
  project_work:      { label: 'Projet',   color: '#34d399' },
  reading:           { label: 'Lecture',  color: '#60a5fa' },
};

// ── Build context payload from current plan ─────────────────────────────────
function buildContext(currentPlan) {
  if (!currentPlan) return null;

  const today = new Date().toLocaleDateString('en-US', { weekday: 'long' });
  const sessions = currentPlan.sessions || [];

  const todaySessions = sessions.filter(s => s.day === today).map(s => ({
    subject_name: s.subject_name,
    task_type: s.task_type,
    start_time: s.start_time?.slice(0, 5),
    end_time: s.end_time?.slice(0, 5),
    completed: s.completed || false,
  }));

  const subjects = [...new Set(sessions.map(s => s.subject_name))];
  const completed = sessions.filter(s => s.completed).length;

  return {
    subjects,
    today_sessions: todaySessions,
    weekly_progress: { completed, total: sessions.length },
    total_hours: currentPlan.total_hours,
  };
}

// ── Typing indicator ─────────────────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div className="flex items-end gap-2 mb-3">
      <div style={{
        width: 28, height: 28, borderRadius: '50%',
        background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 12, flexShrink: 0,
      }}>🤖</div>
      <div style={{
        background: '#f5f3ff', border: '1px solid #e9d5ff',
        borderRadius: '16px 16px 16px 4px', padding: '10px 14px',
        display: 'flex', gap: 5, alignItems: 'center',
      }}>
        {[0, 1, 2].map(i => (
          <span key={i} style={{
            width: 7, height: 7, borderRadius: '50%',
            background: '#7c3aed', display: 'inline-block',
            animation: 'chatBounce 1.2s ease-in-out infinite',
            animationDelay: `${i * 0.2}s`,
          }} />
        ))}
      </div>
    </div>
  );
}

// ── Message bubble ───────────────────────────────────────────────────────────
function MessageBubble({ msg }) {
  const isUser = msg.role === 'user';
  return (
    <div style={{
      display: 'flex', flexDirection: isUser ? 'row-reverse' : 'row',
      alignItems: 'flex-end', gap: 8, marginBottom: 12,
    }}>
      {!isUser && (
        <div style={{
          width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
          background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12,
        }}>🤖</div>
      )}
      <div style={{
        maxWidth: '78%',
        background: isUser
          ? 'linear-gradient(135deg, #7c3aed, #4f46e5)'
          : '#f5f3ff',
        border: isUser ? 'none' : '1px solid #e9d5ff',
        borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
        padding: '10px 14px',
        fontSize: 13.5,
        lineHeight: 1.55,
        color: isUser ? '#fff' : '#3b0764',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
      }}>
        {msg.content}
      </div>
    </div>
  );
}
MessageBubble.propTypes = { msg: PropTypes.object.isRequired };

// ── Main ChatBot component ───────────────────────────────────────────────────
const ChatBot = () => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '👋 Salut ! Je suis ton assistant IA de planning. Pose-moi tes questions sur tes révisions, exercices, ou ton emploi du temps !',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [hasUnread, setHasUnread] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const { currentPlan } = useStudyPlan();

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading, open]);

  // Focus input when opening
  useEffect(() => {
    if (open) {
      setHasUnread(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open]);

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const history = messages.slice(-8); // last 8 messages for context
      const context = buildContext(currentPlan);

      const res = await apiClient.post('/api/v1/chat', {
        message: text,
        context,
        history,
      }, { timeout: 90000 });

      const assistantMsg = { role: 'assistant', content: res.data.reply };
      setMessages(prev => [...prev, assistantMsg]);
      if (!open) setHasUnread(true);
    } catch (err) {
      // Show the real backend error (e.g. "Clé API Colab invalide", "URL ngrok expirée")
      const backendMsg = err.response?.data?.detail;
      const errMsg = {
        role: 'assistant',
        content: backendMsg
          ? `⚠️ ${backendMsg}`
          : '⚠️ Impossible de joindre le serveur IA. Vérifie que le notebook Colab est actif et que l\'URL ngrok est à jour dans le .env.',
      };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, messages, currentPlan, open]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Quick-action suggestions
  const suggestions = [
    "Que dois-je réviser aujourd'hui ?",
    "Génère 3 exercices de maths",
    "Comment optimiser mon planning ?",
  ];

  return (
    <>
      {/* Bounce animation keyframes */}
      <style>{`
        @keyframes chatBounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
          40% { transform: translateY(-6px); opacity: 1; }
        }
        @keyframes chatSlideUp {
          from { opacity: 0; transform: translateY(20px) scale(0.95); }
          to   { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes chatPulse {
          0%, 100% { box-shadow: 0 0 0 0 rgba(124,58,237,0.5); }
          50% { box-shadow: 0 0 0 12px rgba(124,58,237,0); }
        }
      `}</style>

      {/* Floating bubble button */}
      <button
        id="chatbot-toggle-btn"
        onClick={() => setOpen(o => !o)}
        title="Ouvrir l'assistant IA"
        style={{
          position: 'fixed', bottom: 24, right: 24,
          zIndex: 9998,
          width: 56, height: 56, borderRadius: '50%', border: 'none',
          background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
          cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 22, boxShadow: '0 4px 24px rgba(124,58,237,0.5)',
          transition: 'transform 0.2s ease, box-shadow 0.2s ease',
          animation: hasUnread ? 'chatPulse 1.5s infinite' : 'none',
        }}
        onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.12)'}
        onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
      >
        {open ? '✕' : '💬'}
        {hasUnread && !open && (
          <span style={{
            position: 'absolute', top: 4, right: 4,
            width: 10, height: 10, borderRadius: '50%',
            background: '#f87171', border: '2px solid #0f0f1a',
          }} />
        )}
      </button>

      {/* Chat window */}
      {open && (
        <div
          id="chatbot-window"
          style={{
            position: 'fixed', bottom: 92, right: 24, zIndex: 9999,
            width: 380, height: 520,
            background: '#ffffff',
            border: '1px solid #ede9fe',
            borderRadius: 20,
            boxShadow: '0 12px 50px rgba(124,58,237,0.12), 0 0 0 1px rgba(124,58,237,0.05)',
            display: 'flex', flexDirection: 'column',
            animation: 'chatSlideUp 0.25s ease',
            overflow: 'hidden',
          }}
        >
          {/* Header */}
          <div style={{
            padding: '14px 18px',
            background: 'linear-gradient(135deg, #f5f3ff, #e0e7ff)',
            borderBottom: '1px solid #e0e7ff',
            display: 'flex', alignItems: 'center', gap: 10,
          }}>
            <div style={{
              width: 36, height: 36, borderRadius: '50%',
              background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16,
            }}>🤖</div>
            <div>
              <div style={{ color: '#1e1b4b', fontWeight: 700, fontSize: 14 }}>Assistant IA</div>
              <div style={{ color: '#6366f1', fontSize: 11 }}>
                Propulsé par Llama · {currentPlan ? `Plan actif ✅` : 'Aucun plan actif'}
              </div>
            </div>
            <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
              <span style={{
                width: 8, height: 8, borderRadius: '50%',
                background: '#34d399', display: 'inline-block',
                boxShadow: '0 0 6px #34d399',
              }} />
            </div>
          </div>

          {/* Messages area */}
          <div style={{
            flex: 1, overflowY: 'auto', padding: '16px 14px 8px',
            scrollbarWidth: 'thin',
            scrollbarColor: 'rgba(124,58,237,0.3) transparent',
          }}>
            {messages.map((msg, i) => (
              <MessageBubble key={i} msg={msg} />
            ))}
            {loading && <TypingIndicator />}
            <div ref={bottomRef} />
          </div>

          {/* Suggestions (only when no messages from user yet) */}
          {messages.length === 1 && (
            <div style={{ padding: '4px 14px 6px', display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {suggestions.map((s, i) => (
                <button key={i} onClick={() => setInput(s)} style={{
                  background: '#f5f3ff', border: '1px solid #ddd6fe',
                  borderRadius: 20, padding: '5px 10px', fontSize: 11.5,
                  color: '#6d28d9', cursor: 'pointer', transition: 'all 0.15s ease',
                }}
                onMouseEnter={e => e.currentTarget.style.background = '#ede9fe'}
                onMouseLeave={e => e.currentTarget.style.background = '#f5f3ff'}
                >{s}</button>
              ))}
            </div>
          )}

          {/* Input area */}
          <div style={{
            padding: '10px 12px',
            borderTop: '1px solid #f1f5f9',
            display: 'flex', gap: 8, alignItems: 'flex-end',
          }}>
            <textarea
              ref={inputRef}
              id="chatbot-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Pose ta question... (Entrée pour envoyer)"
              rows={1}
              style={{
                flex: 1, background: '#f8fafc',
                border: '1px solid #e2e8f0', borderRadius: 12,
                padding: '9px 12px', color: '#0f172a', fontSize: 13, resize: 'none',
                outline: 'none', fontFamily: 'inherit', lineHeight: 1.4,
                maxHeight: 90, overflowY: 'auto',
                scrollbarWidth: 'thin',
              }}
              onFocus={e => e.target.style.borderColor = '#7c3aed'}
              onBlur={e => e.target.style.borderColor = '#e2e8f0'}
            />
            <button
              id="chatbot-send-btn"
              onClick={sendMessage}
              disabled={!input.trim() || loading}
              style={{
                width: 38, height: 38, borderRadius: '50%', border: 'none',
                background: !input.trim() || loading
                  ? '#f1f5f9'
                  : 'linear-gradient(135deg, #7c3aed, #4f46e5)',
                color: !input.trim() || loading ? '#94a3b8' : '#ffffff',
                cursor: !input.trim() || loading ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 16, transition: 'all 0.2s ease', flexShrink: 0,
              }}
            >
              {loading ? '⏳' : '➤'}
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatBot;
