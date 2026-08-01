'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import type { ChatMessage } from '@/lib/types';
import { fetchChatHistory, deleteChatHistory, loginGuest } from '@/lib/api';

interface ToolIndicator {
  tool: string;
  label: string;
}

export function useChatSSE(veterinaryId: number | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [toolIndicator, setToolIndicator] = useState<ToolIndicator | null>(null);
  const [isHistoryLoaded, setIsHistoryLoaded] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const WELCOME_MSG: ChatMessage = {
    id: 'welcome',
    role: 'bot',
    content: 'Hola, soy tu asistente de Swingtails. Puedo ayudarte a revisar citas, consultar historiales, priorizar pacientes o cancelar turnos. ¿Qué necesitas?',
    isMarkdown: false,
  };

  const loadHistory = useCallback(async () => {
    let isAuthenticated = false;
    try {
      const meRes = await fetch('/api/auth/me');
      if (meRes.ok) {
        isAuthenticated = true;
      }
    } catch {
      isAuthenticated = false;
    }
    if (!isAuthenticated) {
      try {
        await loginGuest();
      } catch (e) {
        console.error("Failed to authenticate guest", e);
      }
    }

    try {
      const data = await fetchChatHistory();
      if (data.history && data.history.length > 0) {
        setMessages(
          data.history.map((msg, i) => ({
            id: `hist-${i}`,
            role: msg.role === 'assistant' ? 'bot' : 'user',
            content: msg.content,
            isMarkdown: msg.role === 'assistant',
          })),
        );
      } else {
        setMessages([WELCOME_MSG]);
      }
    } catch {
      setMessages([WELCOME_MSG]);
    }
    setIsHistoryLoaded(true);
  }, [veterinaryId]);

  useEffect(() => {
    if (veterinaryId !== null || !isHistoryLoaded) {
      loadHistory();
    }
  }, [veterinaryId, loadHistory, isHistoryLoaded]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isStreaming) return;

      const userMsg: ChatMessage = { id: `user-${Date.now()}`, role: 'user', content: text };
      setMessages((prev) => [...prev, userMsg]);

      const streamId = `stream-${Date.now()}`;
      const streamMsg: ChatMessage = { id: streamId, role: 'bot', content: '', isStreaming: true };
      setMessages((prev) => [...prev, streamMsg]);

      setIsStreaming(true);
      setToolIndicator(null);

      try {
        const response = await fetch('/api/chat/stream', {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            question: text,
          }),
        });

        if (response.status === 429) {
          const errData = await response.json().catch(() => null);
          throw new Error(errData?.message || 'Demasiadas solicitudes. Por favor, espera unos minutos antes de intentar de nuevo.');
        }
        if (!response.ok) throw new Error('Network error');

        const reader = response.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let accumulated = '';
        let currentEvent = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop()!;

          for (const line of lines) {
            if (line.startsWith('event: ')) {
              currentEvent = line.slice(7).trim();
            } else if (line.startsWith('data: ') && currentEvent) {
              const jsonStr = line.slice(6).trim();
              if (!jsonStr) continue;
              try {
                const data = JSON.parse(jsonStr);
                switch (currentEvent) {
                  case 'tool_start':
                    setToolIndicator({ tool: data.tool, label: data.label || data.tool });
                    break;
                  case 'token':
                    setToolIndicator(null);
                    accumulated += data.token;
                    setMessages((prev) =>
                      prev.map((m) => (m.id === streamId ? { ...m, content: accumulated } : m)),
                    );
                    break;
                  case 'done':
                    setMessages((prev) =>
                      prev.map((m) =>
                        m.id === streamId ? { ...m, isStreaming: false, isMarkdown: true } : m,
                      ),
                    );
                    break;
                  case 'error':
                    accumulated = data.message;
                    setMessages((prev) =>
                      prev.map((m) =>
                        m.id === streamId ? { ...m, content: data.message, isStreaming: false } : m,
                      ),
                    );
                    break;
                }
              } catch {
                // ignore parse errors
              }
              currentEvent = '';
            }
          }
        }

        if (!accumulated.trim()) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === streamId
                ? { ...m, content: 'No recibí respuesta. Intenta reformular la consulta.', isStreaming: false }
                : m,
            ),
          );
        }
      } catch (error: any) {
        const errorMsg = error?.message || 'Ocurrió un error al procesar tu solicitud.';
        setMessages((prev) =>
          prev.map((m) =>
            m.id === streamId
              ? { ...m, content: errorMsg, isStreaming: false }
              : m,
          ),
        );
      } finally {
        setIsStreaming(false);
        setToolIndicator(null);
      }
    },
    [isStreaming],
  );

  const clearConversation = useCallback(async () => {
    await deleteChatHistory();
    setMessages([WELCOME_MSG]);
  }, []);

  return { messages, isStreaming, toolIndicator, sendMessage, loadHistory, clearConversation };
}
