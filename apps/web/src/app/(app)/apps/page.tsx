"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { RangeKey } from "@/lib/types";
import { formatDuration } from "@/lib/utils";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { RangePicker } from "@/components/dashboard/range-picker";
import { TopAppsChart, HourlyDistributionChart } from "@/components/dashboard/charts";

const CATEGORY_LABEL: Record<string, { variant: "success" | "danger" | "secondary" | "outline"; label: string }> = {
  productive: { variant: "success", label: "Productive" },
  distracting: { variant: "danger", label: "Distracting" },
  neutral: { variant: "secondary", label: "Neutral" },
  unknown: { variant: "outline", label: "Unknown" },
};

export default function AppsPage() {
  const [range, setRange] = React.useState<RangeKey>("7d");
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", range],
    queryFn: () => api.dashboard(range),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">App Usage</h1>
          <p className="text-sm text-muted-foreground">
            Where your time goes — every app, classified.
          </p>
        </div>
        <RangePicker value={range} onChange={setRange} />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          {isLoading || !data ? (
            <Skeleton className="h-72" />
          ) : (
            <HourlyDistributionChart data={data.by_hour} />
          )}
        </div>
        <div>
          {isLoading || !data ? <Skeleton className="h-72" /> : <TopAppsChart data={data.top_apps} />}
        </div>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle>All apps</CardTitle>
          <CardDescription>Sorted by time spent</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading || !data ? (
            <Skeleton className="h-72" />
          ) : data.top_apps.length === 0 ? (
            <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
              No app usage in this range.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-muted-foreground">
                    <th className="py-2 pr-4 font-medium">App</th>
                    <th className="py-2 pr-4 font-medium">Category</th>
                    <th className="py-2 pr-4 font-medium">Time</th>
                    <th className="py-2 pr-4 font-medium">Share</th>
                  </tr>
                </thead>
                <tbody>
                  {data.top_apps.map((a) => {
                    const meta = CATEGORY_LABEL[a.category] ?? CATEGORY_LABEL.unknown;
                    return (
                      <tr key={a.app_name} className="border-b border-border/60 last:border-0">
                        <td className="py-3 pr-4 font-medium">{a.app_name}</td>
                        <td className="py-3 pr-4">
                          <Badge variant={meta.variant}>{meta.label}</Badge>
                        </td>
                        <td className="py-3 pr-4 tabular-nums text-muted-foreground">
                          {formatDuration(a.duration_seconds)}
                        </td>
                        <td className="py-3 pr-4 tabular-nums text-muted-foreground">
                          {Math.round(a.share * 100)}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
