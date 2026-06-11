import Logo from "./Logo";
import Nav from "./Nav";

export default function Shell({ page, setPage, label, children }) {
  return (
    <main className="min-h-screen bg-white p-4">
      <p className="mb-2 text-xs font-bold text-[#8f8f8f]">{label}</p>
      <section className="grid-paper mx-auto min-h-[calc(100vh-3rem)] max-w-[1280px] p-4 sm:p-8 lg:p-10">
        <div className="min-h-[820px] rounded-md border border-smoke bg-white shadow-soft">
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
