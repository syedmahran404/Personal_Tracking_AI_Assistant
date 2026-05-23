"use client";

import * as React from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { format, parseISO } from "date-fns";
import type { AppShare, DayBucket, HourBucket } from "@/lib/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDuration } from "@/lib/utils";

const PROD_COLOR = "hsl(258 90% 66%)";
const DIST_COLOR = "hsl(0 84% 60%)";
const NEUTRAL_COLOR = "hsl(240 5% 64%)";

const tooltipStyle = {
  backgroundColor: "hsl(var(--popover))",
  border: "1px solid hsl(var(--border))",
  borderRadius: 8,
  padding: 8,
  fontSize: 12,
} as const;

// ─── Productivity over time ────────────────────────────────────────────
export function ProductivityTrendChart({ data }: { data: DayBucket[] }) {
  const formatted = data.map((d) => ({
    day: d.day,
    label: format(parseISO(d.day), "MMM d"),
    productive: Math.round(d.productive_seconds / 60),
    distracting: Math.round(d.distracting_seconds / 60),
    coding: Math.round(d.coding_seconds / 60),
    score: d.score,
  }));

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle>Productivity trend</CardTitle>
        <CardDescription>Productive vs. distracting time per day (minutes)</CardDescription>
      </CardHeader>
      <CardContent className="pt-2">
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={formatted} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="prodGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={PROD_COLOR} stopOpacity={0.55} />
                  <stop offset="100%" stopColor={PROD_COLOR} stopOpacity={0} />
                </linearGradient>
                <linearGradient id="distGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={DIST_COLOR} stopOpacity={0.4} />
                  <stop offset="100%" stopColor={DIST_COLOR} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="label" tickLine={false} axisLine={false} fontSize={11}
                stroke="hsl(var(--muted-foreground))" />
              <YAxis tickLine={false} axisLine={false} fontSize={11}
                stroke="hsl(var(--muted-foreground))" />
              <Tooltip
                contentStyle={tooltipStyle}
                formatter={(v: number) => `${v} min`}
              />
              <Area type="monotone" dataKey="productive" stroke={PROD_COLOR} strokeWidth={2} fill="url(#prodGrad)" />
              <Area type="monotone" dataKey="distracting" stroke={DIST_COLOR} strokeWidth={2} fill="url(#distGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── By-hour bar chart ─────────────────────────────────────────────────
export function HourlyDistributionChart({ data }: { data: HourBucket[] }) {
  const formatted = data.map((b) => ({
    hour: `${b.hour.toString().padStart(2, "0")}:00`,
    productive: Math.round(b.productive_seconds / 60),
    distracting: Math.round(b.distracting_seconds / 60),
  }));

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle>Time of day</CardTitle>
        <CardDescription>When you do your best work (UTC)</CardDescription>
      </CardHeader>
      <CardContent className="pt-2">
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={formatted} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="hour" tickLine={false} axisLine={false} fontSize={10}
                stroke="hsl(var(--muted-foreground))" interval={2} />
              <YAxis tickLine={false} axisLine={false} fontSize={11}
                stroke="hsl(var(--muted-foreground))" />
              <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => `${v} min`} />
              <Bar dataKey="productive" stackId="a" fill={PROD_COLOR} radius={[4, 4, 0, 0]} />
              <Bar dataKey="distracting" stackId="a" fill={DIST_COLOR} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Top apps ──────────────────────────────────────────────────────────
const COLOR_BY_CATEGORY: Record<string, string> = {
  productive: PROD_COLOR,
  distracting: DIST_COLOR,
  neutral: NEUTRAL_COLOR,
  unknown: "hsl(240 5% 40%)",
};

export function TopAppsChart({ data }: { data: AppShare[] }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle>Top apps</CardTitle>
        <CardDescription>Where your tracked time went</CardDescription>
      </CardHeader>
      <CardContent className="pt-2">
        {data.length === 0 ? (
          <div className="flex h-56 items-center justify-center text-sm text-muted-foreground">
            No data yet — install the desktop agent to start tracking.
          </div>
        ) : (
          <ul className="space-y-3">
            {data.slice(0, 7).map((a) => {
              const pct = Math.round(a.share * 100);
              const color = COLOR_BY_CATEGORY[a.category] ?? NEUTRAL_COLOR;
              return (
                <li key={a.app_name} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <span
                        className="inline-block h-2 w-2 rounded-full"
                        style={{ background: color }}
                      />
                      <span className="font-medium">{a.app_name}</span>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {formatDuration(a.duration_seconds)} · {pct}%
                    </span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-secondary">
                    <div
                      className="h-full rounded-full transition-[width] duration-500"
                      style={{ width: `${pct}%`, background: color }}
                    />
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Time distribution donut ───────────────────────────────────────────
export function TimeDistributionChart({
  productive,
  neutral,
  distracting,
}: {
  productive: number;
  neutral: number;
  distracting: number;
}) {
  const data = [
    { name: "Productive", value: productive, color: PROD_COLOR },
    { name: "Neutral", value: neutral, color: NEUTRAL_COLOR },
    { name: "Distracting", value: distracting, color: DIST_COLOR },
  ].filter((d) => d.value > 0);

  const total = productive + neutral + distracting;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle>Time distribution</CardTitle>
        <CardDescription>Productive vs. neutral vs. distracting</CardDescription>
      </CardHeader>
      <CardContent className="pt-2">
        <div className="relative h-56 w-full">
          {total === 0 ? (
            <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
              No data yet.
            </div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={data} dataKey="value" innerRadius={60} outerRadius={90} paddingAngle={2}>
                    {data.map((d) => <Cell key={d.name} fill={d.color} />)}
                  </Pie>
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(v: number) => formatDuration(v)}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                <div className="text-2xl font-semibold">{formatDuration(total)}</div>
                <div className="text-xs text-muted-foreground">total tracked</div>
              </div>
            </>
          )}
        </div>
        {data.length > 0 && (
          <div className="mt-4 flex flex-wrap items-center justify-center gap-3 text-xs text-muted-foreground">
            {data.map((d) => (
              <div key={d.name} className="flex items-center gap-1.5">
                <span className="inline-block h-2 w-2 rounded-full" style={{ background: d.color }} />
                {d.name}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Coding heatmap (calendar) ─────────────────────────────────────────
export function CodingHeatmap({ data }: { data: DayBucket[] }) {
  // Compute color intensity from coding_seconds
  const max = Math.max(1, ...data.map((d) => d.coding_seconds));
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle>Coding heatmap</CardTitle>
        <CardDescription>Active coding minutes per day</CardDescription>
      </CardHeader>
      <CardContent className="pt-2">
        <div className="flex flex-wrap gap-1">
          {data.map((d) => {
            const minutes = Math.round(d.coding_seconds / 60);
            const ratio = d.coding_seconds / max;
            const opacity = d.coding_seconds === 0 ? 0.08 : 0.2 + ratio * 0.8;
            return (
              <div
                key={d.day}
                className="h-6 w-6 rounded-sm transition-transform hover:scale-110"
                style={{ backgroundColor: PROD_COLOR, opacity }}
                title={`${format(parseISO(d.day), "MMM d")}: ${minutes} min`}
              />
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
