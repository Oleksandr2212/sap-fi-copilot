import { CopilotMode } from "./types";

const menuItems: Array<{ mode: CopilotMode; label: string; hint: string }> = [
  { mode: "general", label: "Ask Copilot", hint: "Загальні запити по SAP FI" },
  { mode: "error", label: "Explain SAP Error", hint: "Пояснення SAP помилок" },
  { mode: "transaction", label: "Find Transaction", hint: "Пошук транзакцій і кроків" },
  { mode: "guide", label: "How-to Guides", hint: "Практичні покрокові інструкції" },
];

type SidebarProps = {
  activeMode: CopilotMode;
  onChangeMode: (mode: CopilotMode) => void;
};

export default function Sidebar({ activeMode, onChangeMode }: SidebarProps) {
  return (
    <aside className="rounded-2xl border border-sky-900/10 bg-[#0b3f71] p-5 text-white shadow-xl">
      <h1 className="text-xl font-semibold tracking-tight">SAP FI Copilot</h1>
      <p className="mt-2 text-sm text-white/70">Обери режим і став запитання в чаті.</p>

      <div className="mt-6 space-y-2">
        {menuItems.map((item) => {
          const isActive = item.mode === activeMode;
          return (
            <button
              key={item.mode}
              type="button"
              onClick={() => onChangeMode(item.mode)}
              className={[
                "w-full rounded-xl px-3 py-3 text-left transition",
                isActive
                  ? "bg-white text-sky-900 shadow"
                  : "bg-white/10 text-white hover:bg-white/20",
              ].join(" ")}
            >
              <div className="text-sm font-semibold">{item.label}</div>
              <div className={isActive ? "text-xs text-sky-700" : "text-xs text-white/70"}>{item.hint}</div>
            </button>
          );
        })}
      </div>
    </aside>
  );
}
