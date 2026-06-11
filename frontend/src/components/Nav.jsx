import { navItems } from "../data/mockData";

export default function Nav({ page, setPage }) {
  return (
    <nav className="flex flex-wrap items-center gap-3">
      {navItems.map(([id, label]) => (
        <button
          key={id}
          onClick={() => setPage(id)}
          className={`h-11 rounded-md border px-6 text-sm font-black ${
            page === id
              ? "border-pepper bg-pepper text-white"
              : "border-smoke bg-white text-pepper hover:bg-paper"
          }`}
        >
          {label}
        </button>
      ))}
    </nav>
  );
}
