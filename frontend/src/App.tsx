import ThemeToggle from "@/components/theme-toggle";

export default function App() {
  return (
    <div className="min-h-dvh">
      <header className="border-b">
        <div className="mx-auto max-w-5xl px-4 py-3 grid grid-cols-3 items-center">
          <div /> {/* left spacer */}
          <h1 className="justify-self-center text-lg font-semibold tracking-tight">
            Chatbot
          </h1>
          <div className="justify-self-end">
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4">
        {/* Center greeting near the viewport middle */}
        <section className="grid min-h-[calc(100dvh-64px)] place-items-center">
          <p className="text-2xl font-medium">Welcome to Chatbot</p>
        </section>
      </main>
    </div>
  );
}
