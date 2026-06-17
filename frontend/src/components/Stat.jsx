export default function Stat({ label, value, className = "" }) {
  return (
    <div className={`rounded-md border border-smoke bg-white px-4 py-3 ${className}`}>
      <p className="text-xs font-medium text-[#666]">{label}</p>
      <p className="mt-1 text-xl font-black">{value}</p>
    </div>
  );
}
