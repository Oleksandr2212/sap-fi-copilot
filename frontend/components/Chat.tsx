"use client";

import { useEffect, useRef } from "react";

import Message from "./Message";
import { ChatMessage } from "./types";

type ChatProps = {
  messages: ChatMessage[];
  loading: boolean;
};

export default function Chat({ messages, loading }: ChatProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const node = containerRef.current;
    if (!node) {
      return;
    }
    node.scrollTop = node.scrollHeight;
  }, [messages, loading]);

  return (
    <div ref={containerRef} className="flex-1 space-y-4 overflow-y-auto p-4 md:p-6">
      {messages.map((message) => (
        <Message key={message.id} message={message} />
      ))}

      {loading && (
        <div className="flex justify-start">
          <div className="rounded-2xl rounded-bl-sm border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm">
            Copilot думає...
          </div>
        </div>
      )}
    </div>
  );
}
