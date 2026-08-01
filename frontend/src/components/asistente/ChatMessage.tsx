'use client';

import { useEffect, useRef, useState } from 'react';
import { SparklesIcon } from '@/components/ui/Icons';
import { escapeHtml } from '@/lib/utils';
import type { ChatMessage as ChatMessageType } from '@/lib/types';

import DOMPurify from 'dompurify';

export function ChatMessageView({ msg }: { msg: ChatMessageType }) {
  const bodyRef = useRef<HTMLDivElement>(null);
  const [parsedHtml, setParsedHtml] = useState('');

  useEffect(() => {
    if (msg.isMarkdown && msg.content) {
      import('marked').then(({ marked }) => {
        const result = marked.parse(msg.content);
        const sanitize = (rawHtml: string) => typeof window !== 'undefined' ? DOMPurify.sanitize(rawHtml) : rawHtml;
        if (result instanceof Promise) {
          result.then((html) => setParsedHtml(sanitize(html)));
        } else {
          setParsedHtml(sanitize(result));
        }
      });
    }
  }, [msg.content, msg.isMarkdown]);

  if (msg.role === 'user') {
    return (
      <div className="message user">
        <div className="msg-body">{escapeHtml(msg.content)}</div>
      </div>
    );
  }

  return (
    <div className={`message bot ${msg.isStreaming ? '' : ''}`}>
      <span className="msg-avatar"><SparklesIcon /></span>
      <div className="msg-body" ref={bodyRef}>
        {msg.isStreaming ? (
          <div className="streaming-bubble">
            {msg.content}
            <span className="streaming-cursor" />
          </div>
        ) : msg.isMarkdown ? (
          <div dangerouslySetInnerHTML={{ __html: parsedHtml }} />
        ) : (
          <p>{escapeHtml(msg.content)}</p>
        )}
      </div>
    </div>
  );
}

export function ToolIndicatorView({ label }: { label: string }) {
  return (
    <div className="tool-indicator">
      <div className="tool-spinner" />
      <span className="tool-label">{escapeHtml(label)}</span>
    </div>
  );
}
