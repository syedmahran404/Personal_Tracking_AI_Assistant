"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import { LogOut, Moon, Sun, User as UserIcon } from "lucide-react";
import { toast } from "sonner";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";

function initials(text: string) {
  return text
    .split(/\s+|@/)
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase())
    .join("");
}

export function Topbar() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const user = useAuthStore((s) => s.user);
  const clear = useAuthStore((s) => s.clear);
  const router = useRouter();
  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => setMounted(true), []);

  const onLogout = async () => {
    try {
      await api.logout();
    } catch {
      // best-effort
    } finally {
      clear();
      toast.success("Signed out");
      router.push("/login");
    }
  };

  const isDark = (resolvedTheme ?? theme) === "dark";

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-border bg-background/80 px-6 backdrop-blur">
      <div className="text-sm text-muted-foreground">
        Welcome back<span className="text-foreground">{user?.full_name ? `, ${user.full_name}` : ""}</span>
      </div>

      <div className="flex items-center gap-2">
        {mounted && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(isDark ? "light" : "dark")}
            aria-label="Toggle theme"
          >
            {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
        )}

        <div className="ml-2 flex items-center gap-2">
          <Avatar>
            <AvatarFallback>
              {user ? initials(user.full_name || user.email) : <UserIcon className="h-4 w-4" />}
            </AvatarFallback>
          </Avatar>
          <Button variant="ghost" size="icon" onClick={onLogout} aria-label="Sign out">
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  );
}
