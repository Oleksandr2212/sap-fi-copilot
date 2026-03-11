"use client";

import { useState } from "react";

import Chat from "@/components/Chat";
import InputBox from "@/components/InputBox";
import QuickPrompts from "@/components/QuickPrompts";
import Sidebar from "@/components/Sidebar";
import { ChatMessage, CopilotAnswer, CopilotMode } from "@/components/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const modeTitles: Record<CopilotMode, string> = {
  general: "SAP FI Copilot",
  error: "Пояснення SAP помилок",
  transaction: "Пошук SAP транзакцій",
  guide: "How-to інструкції SAP FI",
};

const modePlaceholders: Record<CopilotMode, string> = {
  general: "Наприклад: F5 808, FB60 або як провести оплату постачальнику",
  error: "Введіть код помилки, наприклад F5 808",
  transaction: "Введіть код транзакції, наприклад FB70 або FBL1N",
  guide: "Опишіть процес, наприклад як відкрити період",
};

const modeHints: Record<CopilotMode, string> = {
  general: "Режим Ask Copilot активний.",
  error: "Режим Explain SAP Error активний.",
  transaction: "Режим Find Transaction активний.",
  guide: "Режим How-to Guides активний.",
};

const modeDraftPrompts: Record<CopilotMode, string> = {
  general: "FB03",
  error: "F5 808",
  transaction: "F-47",
  guide: "Як запустити автоматичні платежі?",
};

const initialMessage: ChatMessage = {
  id: "welcome",
  role: "copilot",
  text: "Вітаю! Я SAP FI Copilot. Оберіть режим зліва та поставте питання.",
};

function createId(): string {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function normalizeAnswer(payload: unknown): CopilotAnswer {
  const data = payload as Partial<CopilotAnswer>;
  return {
    type: typeof data?.type === "string" ? data.type : "fallback",
    title: typeof data?.title === "string" ? data.title : "Відповідь",
    reason: typeof data?.reason === "string" ? data.reason : "",
    checks: Array.isArray(data?.checks) ? data.checks.filter((item): item is string => typeof item === "string") : [],
    solution: Array.isArray(data?.solution)
      ? data.solution.filter((item): item is string => typeof item === "string")
      : [],
    tcode: typeof data?.tcode === "string" ? data.tcode : null,
    source: typeof data?.source === "string" ? data.source : null,
  };
}

function extractErrorMessage(payload: unknown): string {
  if (!payload || typeof payload !== "object") {
    return "Сервіс тимчасово недоступний.";
  }

  const maybeDetail = (payload as { detail?: unknown }).detail;
  if (typeof maybeDetail === "string") {
    return maybeDetail;
  }

  return "Сервіс тимчасово недоступний.";
}

export default function Home() {
  const [activeMode, setActiveMode] = useState<CopilotMode>("general");
  const [input, setInput] = useState(modeDraftPrompts.general);
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([initialMessage]);

  const submitMessage = async (rawMessage: string, mode: CopilotMode) => {
    const message = rawMessage.trim();
    if (!message || loading) {
      return;
    }

    setMessages((prev) => [...prev, { id: createId(), role: "user", text: message }]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message, mode }),
      });

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(extractErrorMessage(payload));
      }

      const answer = normalizeAnswer(payload);

      setMessages((prev) => [
        ...prev,
        {
          id: createId(),
          role: "copilot",
          text: answer.reason || answer.title,
          answer,
        },
      ]);
    } catch (error) {
      const fallback = error instanceof Error ? error.message : "Невідома помилка запиту.";
      setMessages((prev) => [
        ...prev,
        {
          id: createId(),
          role: "copilot",
          text: fallback,
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    await submitMessage(input, activeMode);
  };

  const handleQuickPrompt = async (prompt: string) => {
    setInput(prompt);
    await submitMessage(prompt, activeMode);
  };

  const handleModeChange = (mode: CopilotMode) => {
    if (mode === activeMode) {
      return;
    }

    setActiveMode(mode);
    setInput(modeDraftPrompts[mode]);
    setMessages((prev) => [
      ...prev,
      {
        id: createId(),
        role: "copilot",
        text: `${modeHints[mode]} Приклад запиту: ${modeDraftPrompts[mode]}`,
      },
    ]);
  };

  return (
    <main className="min-h-screen p-4 md:p-6">
      <div className="mx-auto grid h-[calc(100vh-2rem)] max-w-7xl gap-4 lg:grid-cols-[280px_minmax(0,1fr)] md:h-[calc(100vh-3rem)]">
        <Sidebar activeMode={activeMode} onChangeMode={handleModeChange} />

        <section className="flex min-h-0 flex-col rounded-2xl border border-slate-200 bg-slate-50/80 shadow-xl backdrop-blur">
          <header className="border-b border-slate-200 px-4 py-4 md:px-6">
            <h2 className="text-lg font-semibold text-slate-900 md:text-xl">{modeTitles[activeMode]}</h2>
            <p className="mt-1 text-sm text-slate-600">Всі відповіді формуються українською мовою.</p>
          </header>

          <QuickPrompts mode={activeMode} disabled={loading} onSelect={handleQuickPrompt} />

          <Chat messages={messages} loading={loading} />

          <InputBox
            value={input}
            placeholder={modePlaceholders[activeMode]}
            disabled={loading}
            onChange={setInput}
            onSubmit={sendMessage}
          />
        </section>
      </div>
    </main>
  );
}
