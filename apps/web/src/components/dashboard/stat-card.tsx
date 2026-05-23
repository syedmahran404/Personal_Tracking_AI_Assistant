"use client";

import * as React from "react";
import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";

interface StatCardProps {
  label: string;
  value: React.ReactNode;
  icon: LucideIcon;
  hint?: string;
  trend?: { value: string; positive?: boolean };
  accent?: "primary" | "success" | "warning" | "danger";
}

export function StatCard({ label, value, icon: Icon, hint, trend, accent = "primary" }: StatCardProps) {
  const accentClasses: Record<NonNullable<StatCardProps["accent"]>, string> = {
    primary: "from-brand-500/20 to-brand-700/0 text-primary",
    success: "from-success/20 to-success/0 text-success",
    warning: "from-warning/20 to-warning/0 text-warning",
    danger: "from-danger/20 to-danger/0 text-danger",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <Card className="relative overflow-hidden p-5">
        <div
          className={cn(
            "pointer-events-none absolute -right-12 -top-12 h-40 w-40 rounded-full bg-gradient-to-br opacity-60 blur-2xl",
            accentClasses[accent],
          )}
        />
        <div className="flex items-start justify-between">
          <div>
            <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</div>
            <div className="mt-2 text-3xl font-semibold tracking-tight">{value}</div>
            {(hint || trend) && (
              <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                {trend && (
                  <span className={cn(trend.positive ? "text-success" : "text-danger")}>
                    {trend.positive ? "▲" : "▼"} {trend.value}
                  </span>
                )}
                {hint}
              </div>
            )}
          </div>
          <div className={cn("rounded-lg border border-border bg-background/40 p-2", accentClasses[accent])}>
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
