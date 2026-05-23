"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { Code2, GitBranch, Keyboard, Layers } from "lucide-react";

import { api } from "@/lib/api";
import type { RangeKey } from "@/lib/types";
import { formatDuration } from "@/lib/utils";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatCard } from "@/components/dashboard/stat-card";
import { RangePicker } from "@/components/dashboard/range-picker";

export default function CodingPage() {
  const [range, setRange] = React.useState<RangeKey>("30d");
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", range],
    queryFn: () => api.dashboard(range),
  });

  const totalLangSeconds = (data?.coding.languages ?? []).reduce((s, l) => s + l.seconds, 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Coding</h1>
          <p className="text-sm text-muted-foreground">
            Languages, projects, and editor activity from your IDE.
          </p>
        </div>
        <RangePicker value={range} onChange={setRange} />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {isLoading || !data ? (
          [...Array(4)].map((_, i) => <Skeleton key={i} className="h-28" />)
        ) : (
          <>
            <StatCard
              label="Active coding"
              value={formatDuration(data.coding.active_seconds)}
              icon={Keyboard}
              accent="primary"
              hint="Excludes idle time"
            />
            <StatCard
              label="Total in IDE"
              value={formatDuration(data.coding.total_seconds)}
              icon={Code2}
              accent="success"
            />
            <StatCard
              label="Sessions"
              value={data.coding.sessions.toString()}
              icon={Layers}
              accent="warning"
            />
            <StatCard
              label="Top language"
              value={data.coding.languages[0]?.language ?? "—"}
              icon={GitBranch}
              accent="danger"
              hint={
                data.coding.languages[0]
                  ? formatDuration(data.coding.languages[0].seconds)
                  : "Track an IDE session to populate"
              }
            />
          </>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle>Languages</CardTitle>
            <CardDescription>Active time per language</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading || !data ? (
              <Skeleton className="h-44" />
            ) : data.coding.languages.length === 0 ? (
              <EmptyState text="No coding sessions in this range." />
            ) : (
              <ul className="space-y-3">
                {data.coding.languages.map((l) => {
                  const pct = totalLangSeconds ? Math.round((l.seconds / totalLangSeconds) * 100) : 0;
                  return (
                    <li key={l.language} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">{l.language}</span>
                        <span className="text-xs text-muted-foreground">
                          {formatDuration(l.seconds)} · {pct}%
                        </span>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-secondary">
                        <div
                          className="h-full rounded-full bg-primary transition-[width] duration-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle>Projects</CardTitle>
            <CardDescription>Active time per project</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading || !data ? (
              <Skeleton className="h-44" />
            ) : data.coding.projects.length === 0 ? (
              <EmptyState text="No projects detected." />
            ) : (
              <ul className="space-y-3">
                {data.coding.projects.map((p) => (
                  <li key={p.project} className="flex items-center justify-between text-sm">
                    <span className="font-medium">{p.project}</span>
                    <span className="text-xs text-muted-foreground">
                      {formatDuration(p.seconds)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="flex h-44 items-center justify-center text-sm text-muted-foreground">{text}</div>
  );
}
