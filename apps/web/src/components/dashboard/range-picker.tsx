"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { RangeKey } from "@/lib/types";

const OPTS: { value: RangeKey; label: string }[] = [
  { value: "today", label: "Today" },
  { value: "7d", label: "7 days" },
  { value: "30d", label: "30 days" },
  { value: "90d", label: "90 days" },
];

export function RangePicker({
  value,
  onChange,
}: {
  value: RangeKey;
  onChange: (v: RangeKey) => void;
}) {
  return (
    <Tabs value={value} onValueChange={(v) => onChange(v as RangeKey)}>
      <TabsList>
        {OPTS.map((o) => (
          <TabsTrigger key={o.value} value={o.value}>
            {o.label}
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}
