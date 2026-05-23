import Link from "next/link";
import { Activity } from "lucide-react";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="relative grid min-h-screen overflow-hidden lg:grid-cols-2">
      {/* Left: form */}
      <div className="flex flex-col px-6 py-10 sm:px-12">
        <Link href="/" className="flex items-center gap-2">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-brand-400 to-brand-700 shadow-lg shadow-primary/30">
            <Activity className="h-4 w-4 text-white" />
          </div>
          <span className="text-base font-semibold">Pulse</span>
        </Link>
        <div className="flex flex-1 items-center justify-center">
          <div className="w-full max-w-sm">{children}</div>
        </div>
      </div>

      {/* Right: artwork */}
      <div className="relative hidden overflow-hidden bg-muted lg:block">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-700/30 via-brand-500/20 to-background" />
        <div className="absolute inset-0 bg-grid-pattern bg-[size:48px_48px] opacity-20" />
        <div className="absolute left-1/2 top-1/2 h-[480px] w-[480px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/30 blur-3xl" />

        <div className="relative flex h-full flex-col justify-end p-12">
          <blockquote className="space-y-2">
            <p className="text-2xl font-medium leading-snug text-foreground">
              “I shipped 3× more in the first month — not because I worked more, but because Pulse
              told me <span className="text-primary">when</span> I do my best work.”
            </p>
            <footer className="text-sm text-muted-foreground">— Senior engineer, Series B startup</footer>
          </blockquote>
        </div>
      </div>
    </main>
  );
}
