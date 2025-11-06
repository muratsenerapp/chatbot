import Chat from "@/components/chat/Chat";
import ThemeToggle from "@/components/theme-toggle";

export default function App() {
  return (
    <div className="min-h-dvh">
      <header className="border-b">
        <div className="mx-auto grid max-w-5xl grid-cols-3 items-center px-4 py-3">
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
        <Chat />
      </main>
    </div>
  );
}
