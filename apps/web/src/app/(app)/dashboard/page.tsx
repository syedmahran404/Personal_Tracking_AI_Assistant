"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, Code2, Flame, Target, Timer, TrendingUp } from "lucide-react";

import { api } from "@/lib/api";
import type { RangeKey } from "@/lib/types";
import { formatDuration } from "@/lib/utils";

import { StatCard } from "@/components/dashboard/stat-card";
import { RangePicker } from "@/components/dashboard/range-picker";
import {
  CodingHeatmap,
  HourlyDistributionChart,
  ProductivityTrendChart,
  TimeDistributionChart,
  TopAppsChart,
} from "@/components/dashboard/charts";
import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardPage() {
  const [range, setRange] = React.useState<RangeKey>("7d");
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard", range],
    queryFn: () => api.dashboard(range),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            A live view of your focus, distractions, and coding output.
          </p>
        </div>
        <RangePicker value={range} onChange={setRange} />
      </div>

      {error ? (
        <div className="rounded-lg border border-danger/40 bg-danger/10 p-4 text-sm text-danger">
          Failed to load analytics. Make sure the API is running and try again.
        </div>
      ) : null}

      {/* KPI row */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {isLoading || !data ? (
          [...Array(4)].map((_, i) => <Skeleton key={i} className="h-28" />)
        ) : (
          <>
            <StatCard
              label="Productivity Score"
              value={`${data.productivity.score.toFixed(0)}`}
              hint="0–100, weighted across categories"
              icon={TrendingUp}
              accent="primary"
            />
            <StatCard
              label="Focus Score"
              value={`${data.productivity.focus_score.toFixed(0)}`}
              hint="Long uninterrupted blocks reward this"
              icon={Target}
              accent="success"
            />
            <StatCard
              label="Coding (active)"
              value={formatDuration(data.coding.active_seconds)}
              hint={`${data.coding.sessions} sessions`}
              icon={Code2}
              accent="warning"
            />
            <StatCard
              label="Streak"
              value={`${data.streak.current_streak_days}d`}
              hint={`Longest: ${data.streak.longest_streak_days}d`}
              icon={Flame}
              accent="danger"
            />
          </>
        )}
      </div>

      {/* Charts row 1 */}
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          {isLoading || !data ? (
            <Skeleton className="h-80" />
          ) : (
            <ProductivityTrendChart data={data.by_day} />
          )}
        </div>
        <div>
          {isLoading || !data ? (
            <Skeleton className="h-80" />
          ) : (
            <TimeDistributionChart
              productive={data.productivity.productive_seconds}
              neutral={data.productivity.neutral_seconds}
              distracting={data.productivity.distracting_seconds}
            />
          )}
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          {isLoading || !data ? (
            <Skeleton className="h-72" />
          ) : (
            <HourlyDistributionChart data={data.by_hour} />
          )}
        </div>
        <div>
          {isLoading || !data ? (
            <Skeleton className="h-72" />
          ) : (
            <TopAppsChart data={data.top_apps} />
          )}
        </div>
      </div>

      {/* Heatmap row */}
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          {isLoading || !data ? <Skeleton className="h-44" /> : <CodingHeatmap data={data.by_day} />}
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
          <StatCard
            label="Today productive"
            value={data ? formatDuration(data.streak.today_productive_seconds) : <Skeleton className="h-7 w-20" />}
            icon={Timer}
            accent="primary"
          />
          <StatCard
            label="Total tracked"
            value={data ? formatDuration(data.productivity.total_tracked_seconds) : <Skeleton className="h-7 w-20" />}
            icon={Activity}
            accent="success"
          />
        </div>
      </div>
    </div>
  );
}
