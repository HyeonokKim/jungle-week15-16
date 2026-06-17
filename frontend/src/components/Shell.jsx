import Logo from "./Logo";
import Nav from "./Nav";

export default function Shell({ page, setPage, label, children }) {
  return (
    <main className="min-h-screen min-w-0 bg-white p-0">
      <section className="grid-paper min-h-screen w-full min-w-0 p-2 sm:p-6 lg:p-8">
        <p className="mb-2 text-xs font-bold text-[#8f8f8f]">{label}</p>
        <div className="min-h-[calc(100vh-5rem)] min-w-0 rounded-md border border-smoke bg-white shadow-soft">
          <header className="flex flex-col gap-5 border-b border-ash px-5 py-6 md:flex-row md:items-center md:justify-between lg:px-8 lg:py-8">
            <Logo />
            {page !== "login" && <Nav page={page} setPage={setPage} />}
          </header>
          {children}
        </div>
      </section>
    </main>
  );
}
