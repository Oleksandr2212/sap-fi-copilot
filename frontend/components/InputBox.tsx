type InputBoxProps = {
  value: string;
  placeholder: string;
  disabled?: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
};

export default function InputBox({ value, placeholder, disabled = false, onChange, onSubmit }: InputBoxProps) {
  return (
    <form
      className="border-t border-slate-200 bg-white p-4"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <div className="flex gap-3">
        <input
          className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-sky-500"
          value={value}
          placeholder={placeholder}
          onChange={(event) => onChange(event.target.value)}
          disabled={disabled}
        />
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="rounded-xl bg-sky-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-800 disabled:cursor-not-allowed disabled:bg-slate-400"
        >
          Надіслати
        </button>
      </div>
    </form>
  );
}
