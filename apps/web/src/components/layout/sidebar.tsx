"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  Activity,
  AppWindow,
  Code2,
  LayoutDashboard,
  MessagesSquare,
  Settings,
  Sparkles,
} from "lucide-react";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/coding", label: "Coding", icon: Code2 },
  { href: "/apps", label: "App Usage", icon: AppWindow },
  { href: "/insights", label: "Insights", icon: Sparkles },
  { href: "/chat", label: "AI Chat", icon: MessagesSquare },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-border bg-card/40 px-3 py-4 lg:flex">
      <Link href="/dashboard" className="mb-8 flex items-center gap-2 px-2">
        <div className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-brand-400 to-brand-700 shadow-lg shadow-primary/30">
          <Activity className="h-4 w-4 text-white" />
        </div>
        <span className="text-base font-semibold">Pulse</span>
      </Link>

      <nav className="flex flex-1 flex-col gap-1">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname?.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "group flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-accent text-foreground"
                  : "text-muted-foreground hover:bg-accent/60 hover:text-foreground",
              )}
            >
              <Icon
                className={cn(
                  "h-4 w-4 transition-colors",
                  active ? "text-primary" : "text-muted-foreground group-hover:text-foreground",
                )}
              />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-2 rounded-lg border border-dashed border-border p-3 text-xs text-muted-foreground">
        <div className="font-medium text-foreground">Tip</div>
        <div className="mt-1">
          Install the desktop agent to start tracking your app usage automatically.
        </div>
      </div>
    </aside>
  );
}
