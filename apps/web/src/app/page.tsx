import Link from "next/link";
import { ArrowRight, Activity, Brain, Code2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-background">
      {/* Background grid + glow */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-grid-pattern bg-[size:32px_32px] opacity-30" />
      <div className="pointer-events-none absolute left-1/2 top-0 -z-10 h-[700px] w-[1000px] -translate-x-1/2 rounded-full bg-primary/20 blur-3xl" />

      <header className="container flex h-16 items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-brand-400 to-brand-700 shadow-lg shadow-primary/30">
            <Activity className="h-4 w-4 text-white" />
          </div>
          <span className="text-base font-semibold">Pulse</span>
        </div>
        <nav className="flex items-center gap-2">
          <Button asChild variant="ghost">
            <Link href="/login">Sign in</Link>
          </Button>
          <Button asChild>
            <Link href="/signup">
              Get started <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </Button>
        </nav>
      </header>

      <section className="container flex flex-col items-center pt-24 text-center sm:pt-32">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-background/40 px-3 py-1 text-xs text-muted-foreground backdrop-blur">
          <Sparkles className="h-3 w-3 text-primary" />
          AI-powered productivity intelligence
        </div>
        <h1 className="max-w-3xl bg-gradient-to-b from-foreground to-foreground/60 bg-clip-text text-5xl font-semibold tracking-tight text-transparent sm:text-6xl">
          Understand your work the way <span className="text-primary">it actually happens.</span>
        </h1>
        <p className="mt-6 max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg">
          Pulse silently tracks the apps you use, the code you write, and the time you spend —
          then turns it into focus scores, weekly reports, and an assistant that knows your patterns.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Button asChild size="lg">
            <Link href="/signup">
              Start tracking free <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button asChild size="lg" variant="outline">
            <Link href="/login">Try the demo</Link>
          </Button>
        </div>
      </section>

      <section className="container mt-28 grid gap-4 pb-24 md:grid-cols-3">
        {[
          {
            icon: Activity,
            title: "App usage tracking",
            desc: "Know exactly where your hours go — with productive vs. distracting classification baked in.",
          },
          {
            icon: Code2,
            title: "Coding analytics",
            desc: "Per-language and per-project time, deep-work blocks, and commit cadence.",
          },
          {
            icon: Brain,
            title: "AI insights",
            desc: "Weekly summaries, distraction alerts, and a chat assistant grounded in your data.",
          },
        ].map(({ icon: Icon, title, desc }) => (
          <div
            key={title}
            className="group rounded-2xl border border-border bg-card p-6 transition-all hover:border-primary/40 hover:shadow-lg hover:shadow-primary/5"
          >
            <div className="mb-4 grid h-10 w-10 place-items-center rounded-lg bg-primary/10 text-primary transition-transform group-hover:scale-110">
              <Icon className="h-5 w-5" />
            </div>
            <h3 className="font-semibold">{title}</h3>
            <p className="mt-2 text-sm text-muted-foreground">{desc}</p>
          </div>
        ))}
      </section>
    </main>
  );
}
