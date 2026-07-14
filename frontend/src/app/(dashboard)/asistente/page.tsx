'use client';

import { useState, useEffect, useRef, FormEvent, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useDashboard } from '@/contexts/DashboardContext';
import { useChatSSE } from '@/hooks/useChatSSE';
import { ChatMessageView, ToolIndicatorView } from '@/components/asistente/ChatMessage';
import { SparklesIcon, ArrowRightIcon, RefreshIcon, InfoIcon } from '@/components/ui/Icons';

const SUGGEST_PROMPTS = [
  'Dame un resumen del día',
  'Crea una cita',
  'Muéstrame el historial de un paciente',
  'Prioriza los pacientes de hoy',
];

const SIDE_PROMPTS = [
  '¿Cuántas citas hay hoy y cuántas están pendientes?',
  '¿Qué pacientes tienen más visitas registradas?',
  'Dame un análisis de la carga de citas de esta semana',
  'Confirma todas las citas pendientes de hoy',
];

export default function AsistentePage() {
  const { selectedVetId } = useDashboard();
  const router = useRouter();
  const vetId = selectedVetId ? parseInt(selectedVetId, 10) : null;
  const { messages, isStreaming, toolIndicator, sendMessage, clearConversation } = useChatSSE(vetId);
  const [input, setInput] = useState('');
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages, toolIndicator]);

  useEffect(() => {
    const pending = localStorage.getItem('pending_ai_prompt');
    if (pending) {
      localStorage.removeItem('pending_ai_prompt');
      sendMessage(pending);
    }
  }, [sendMessage]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    sendMessage(input.trim());
    setInput('');
  };

  const handleAskAI = useCallback((prompt: string) => {
    sendMessage(prompt);
  }, [sendMessage]);

  const handleNavigate = useCallback((path: string) => {
    router.push(path);
  }, [router]);

  return (
    <div className="view view-ai active" style={{ display: 'flex', height: '100%' }}>
      <div className="ai-layout">
        <div className="ai-chat">
          <div className="ai-header">
            <div className="ai-id">
              <span className="ai-avatar"><SparklesIcon /></span>
              <div>
                <h2 className="panel-title">Asistente IA</h2>
                <p className="panel-sub">Análisis, historiales y gestión de citas</p>
              </div>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={clearConversation} title="Empezar conversación nueva">
              <RefreshIcon /> Nueva
            </button>
          </div>

          <div className="chat-scroll" ref={chatRef}>
            {messages.map((msg) => (
              <ChatMessageView key={msg.id} msg={msg} />
            ))}
            {toolIndicator && <ToolIndicatorView label={toolIndicator.label} />}
          </div>

          <div className="chat-foot">
            <div className="suggest-row">
              {SUGGEST_PROMPTS.map((p) => (
                <button key={p} className="suggest" onClick={() => handleAskAI(p)}>{p}</button>
              ))}
            </div>
            <form className="chat-input" onSubmit={handleSubmit}>
              <input
                type="text"
                placeholder="Escribe una consulta para el asistente…"
                autoComplete="off"
                aria-label="Mensaje al asistente"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={isStreaming}
              />
              <button type="submit" className="send-btn" disabled={isStreaming || !input.trim()} aria-label="Enviar">
                <ArrowRightIcon />
              </button>
            </form>
          </div>
        </div>

        <aside className="ai-side" aria-label="Sugerencias y acciones">
          <div className="side-block">
            <h3 className="side-title">Preguntas sugeridas</h3>
            <div className="side-prompts">
              {SIDE_PROMPTS.map((p) => (
                <button key={p} className="side-prompt" onClick={() => handleAskAI(p)}>{p}</button>
              ))}
            </div>
          </div>
          <div className="side-note">
            <span className="side-note-ic"><InfoIcon /></span>
            <p>El asistente puede crear, confirmar y cancelar citas usando las funciones conectadas al sistema.</p>
          </div>
        </aside>
      </div>
    </div>
  );
}
