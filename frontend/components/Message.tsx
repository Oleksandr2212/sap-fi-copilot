import { ChatMessage } from "./types";

type MessageProps = {
  message: ChatMessage;
};

export default function Message({ message }: MessageProps) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-sky-700 px-4 py-3 text-sm text-white shadow">
          {message.text}
        </div>
      </div>
    );
  }

  if (!message.answer) {
    return (
      <div className="flex justify-start">
        <div
          className={[
            "max-w-[90%] rounded-2xl rounded-bl-sm border px-4 py-3 text-sm shadow-sm",
            message.isError ? "border-red-200 bg-red-50 text-red-800" : "border-slate-200 bg-white text-slate-800",
          ].join(" ")}
        >
          {message.text}
        </div>
      </div>
    );
  }

  const { answer } = message;

  const checksHeading =
    answer.type === "transaction_help"
      ? "Перед виконанням перевірте"
      : answer.type === "how_to_guide"
        ? "Підготовка"
        : "Що перевірити";

  const solutionHeading =
    answer.type === "transaction_help"
      ? "Рекомендована послідовність дій"
      : answer.type === "how_to_guide"
        ? "Покроковий сценарій"
        : "Що зробити";

  return (
    <div className="flex justify-start">
      <div className="max-w-[90%] rounded-2xl rounded-bl-sm border border-slate-200 bg-white px-4 py-4 text-sm text-slate-800 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900">{answer.title}</h3>

        <p className="mt-2 whitespace-pre-line leading-relaxed">{answer.reason}</p>

        {answer.checks.length > 0 && (
          <div className="mt-3">
            <p className="font-semibold text-slate-900">{checksHeading}</p>
            <ul className="mt-1 list-disc space-y-1 pl-5">
              {answer.checks.map((item, index) => (
                <li key={`${item}-${index}`}>{item}</li>
              ))}
            </ul>
          </div>
        )}

        {answer.solution.length > 0 && (
          <div className="mt-3">
            <p className="font-semibold text-slate-900">{solutionHeading}</p>
            <ul className="mt-1 list-disc space-y-1 pl-5">
              {answer.solution.map((item, index) => (
                <li key={`${item}-${index}`}>{item}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-3 flex flex-wrap items-center gap-2">
          {answer.tcode && (
            <div className="inline-flex rounded-lg bg-sky-100 px-3 py-1 text-xs font-semibold text-sky-900">
              T-code: {answer.tcode}
            </div>
          )}

          {answer.source && (
            <a
              href={answer.source}
              target="_blank"
              rel="noreferrer"
              className="inline-flex rounded-lg bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-200"
            >
              Джерело
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
