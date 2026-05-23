"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { AlertTriangle, Loader2, Sparkles, TrendingUp } from "lucide-react";
import { toast } from "sonner";
import { format, parseISO } from "date-fns";

import { api } from "@/lib/api";
import type { InsightKind, InsightPublic } from "@/lib/types";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

const KIND_META: Record<InsightKind, { label: string; variant: "default" | "warning" | "danger" | "success" }> = {
  weekly_summary: { label: "Weekly", variant: "default" },
  daily_summary: { label: "Daily", variant: "default" },
  distraction_alert: { label: "Distraction", variant: "danger" },
  burnout_warning: { label: "Burnout", variant: "warning" },
  focus_tip: { label: "Focus tip", variant: "default" },
  streak: { label: "Streak", variant: "success" },
  recommendation: { label: "Tip", variant: "default" },
};

export default function InsightsPage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["insights"],
    queryFn: () => api.insights(),
  });

  const generate = useMutation({
    mutationFn: () => api.generateWeekly(),
    onSuccess: () => {
      toast.success("Weekly summary generated");
      qc.invalidateQueries({ queryKey: ["insights"] });
    },
    onError: () => toast.error("Failed to generate summary"),
  });

  const scan = useMutation({
    mutationFn: () => api.scanDistraction(),
    onSuccess: (insight) => {
      if (insight) {
        toast.success("Distraction alert created");
        qc.invalidateQueries({ queryKey: ["insights"] });
      } else {
        toast.message("All good — no alert needed today");
      }
    },
    onError: () => toast.error("Scan failed"),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">AI Insights</h1>
          <p className="text-sm text-muted-foreground">
            Reports, alerts, and tips generated from your tracking data.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => scan.mutate()}
            disabled={scan.isPending}
          >
            {scan.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <AlertTriangle className="h-4 w-4" />}
            Scan distractions
          </Button>
          <Button onClick={() => generate.mutate()} disabled={generate.isPending}>
            {generate.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            Generate weekly summary
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-44" />)}
        </div>
      ) : !data || data.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center gap-3 py-16 text-center">
            <div className="grid h-12 w-12 place-items-center rounded-full bg-primary/10 text-primary">
              <TrendingUp className="h-5 w-5" />
            </div>
            <CardTitle className="text-lg">No insights yet</CardTitle>
            <CardDescription className="max-w-sm">
              Generate your first weekly summary or run a quick distraction scan to surface patterns
              from your tracked activity.
            </CardDescription>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {data.map((i, idx) => (
            <InsightCard key={i.id} insight={i} delay={idx * 0.04} />
          ))}
        </div>
      )}
    </div>
  );
}

function InsightCard({ insight, delay }: { insight: InsightPublic; delay: number }) {
  const meta = KIND_META[insight.kind] ?? KIND_META.recommendation;
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, delay }}>
      <Card className="h-full">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="text-base">{insight.title}</CardTitle>
            <Badge variant={meta.variant}>{meta.label}</Badge>
          </div>
          <CardDescription>{format(parseISO(insight.created_at), "MMM d, yyyy · HH:mm")}</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="whitespace-pre-line text-sm leading-relaxed text-foreground/90">
            {insight.body}
          </p>
          {insight.score != null && (
            <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
              <span>Score</span>
              <span className="font-medium text-foreground">{insight.score.toFixed(0)}</span>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
