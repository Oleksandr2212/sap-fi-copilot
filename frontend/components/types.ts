export type CopilotMode = "general" | "error" | "transaction" | "guide";

export type CopilotAnswer = {
  type: string;
  title: string;
  reason: string;
  checks: string[];
  solution: string[];
  tcode: string | null;
  source: string | null;
};

export type ChatMessage = {
  id: string;
  role: "user" | "copilot";
  text: string;
  answer?: CopilotAnswer;
  isError?: boolean;
};
