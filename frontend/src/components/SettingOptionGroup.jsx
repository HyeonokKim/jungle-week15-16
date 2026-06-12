export default function SettingOptionGroup({ label, value, options, onChange, disabled = false }) {
  return (
    <div className={`rounded-md border border-smoke bg-white px-4 py-4 ${disabled ? "opacity-50" : ""}`}>
      <p className="text-xs font-medium text-[#666]">{label}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {options.map((option) => {
          const isSelected = option.value === value;
          return (
            <button
              key={String(option.value)}
              type="button"
              disabled={disabled}
              onClick={() => onChange(option.value)}
              className={`rounded-md border px-3 py-2 text-sm font-black transition ${
                isSelected
                  ? "border-pepper bg-pepper text-white"
                  : "border-smoke bg-white text-pepper hover:border-pepper"
              }`}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
