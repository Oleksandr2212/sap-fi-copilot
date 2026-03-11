import { CopilotMode } from "./types";

const modePrompts: Record<CopilotMode, string[]> = {
  general: [
    "F5 808",
    "F5 117",
    "F5 736",
    "F5 263",
    "FB60",
    "FB70",
    "FBL1N",
    "FBL5N",
    "F110",
    "OB52",
    "OB08",
    "FBRA",
    "F-47",
    "F-53",
    "FS00",
    "FB03",
    "AFAB",
    "Як запустити автоматичні платежі?",
    "Як відкрити період для проводок?",
    "Як провести рахунок від постачальника?",
  ],
  error: [
    "F5 808",
    "F5 263",
    "F5 117",
    "F5 312",
    "F5 701",
    "F5 702",
    "F5 727",
    "F5 734",
    "F5 736",
    "F5 052",
    "Поясни F5 808",
    "Поясни F5 117",
    "Поясни F5 263",
    "Поясни F5 736",
    "Що означає F5 701?",
    "Що перевірити при F5 312?",
    "Як виправити F5 727?",
    "Що робити при F5 734?",
    "Помилка F5 702",
    "Помилка F5 052",
  ],
  transaction: [
    "FB60",
    "FB65",
    "FB70",
    "FB75",
    "FB50",
    "FB01",
    "FB03",
    "FB08",
    "FBRA",
    "FBL1N",
    "FBL5N",
    "FBL3N",
    "FS00",
    "FS10N",
    "F-28",
    "F-53",
    "F-44",
    "F110",
    "OB52",
    "AFAB",
  ],
  guide: [
    "Як провести рахунок від постачальника?",
    "Як провести рахунок клієнту?",
    "Як виконати вхідний платіж від клієнта?",
    "Як виконати вихідний платіж постачальнику?",
    "Як запустити автоматичні платежі?",
    "Як відкрити період для проводок?",
    "Як виконати ручне очищення постачальника?",
    "Як переглянути позиції постачальника?",
    "Як провести FB60 крок за кроком?",
    "Як провести FB70 крок за кроком?",
    "Як працювати з F-28?",
    "Як працювати з F-53?",
    "Як очищувати позиції через F-44?",
    "Як перевірити документи у FBL1N?",
    "Як перевірити документи у FBL5N?",
    "Як підготувати запуск F110?",
    "Як перевірити відкритий період в OB52?",
    "Як виконати оплату постачальнику?",
    "Як закрити дебіторську заборгованість?",
    "Як діяти, якщо документ не проводиться?",
  ],
};

type QuickPromptsProps = {
  mode: CopilotMode;
  disabled?: boolean;
  onSelect: (prompt: string) => void;
};

export default function QuickPrompts({ mode, disabled = false, onSelect }: QuickPromptsProps) {
  return (
    <div className="border-b border-slate-200 bg-white/80 px-4 py-3 md:px-6">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Швидкі запити</p>
      <div className="flex flex-wrap gap-2">
        {modePrompts[mode].map((prompt) => (
          <button
            key={prompt}
            type="button"
            disabled={disabled}
            onClick={() => onSelect(prompt)}
            className="rounded-full border border-sky-200 bg-sky-50 px-3 py-1.5 text-xs font-medium text-sky-900 transition hover:bg-sky-100 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
