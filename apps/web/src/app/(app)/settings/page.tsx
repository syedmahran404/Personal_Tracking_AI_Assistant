"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Monitor } from "lucide-react";
import { toast } from "sonner";
import { format, parseISO } from "date-fns";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuthStore } from "@/stores/auth";

export default function SettingsPage() {
  const qc = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);

  const [fullName, setFullName] = React.useState(user?.full_name ?? "");
  const [tz, setTz] = React.useState(user?.timezone ?? "UTC");

  React.useEffect(() => {
    setFullName(user?.full_name ?? "");
    setTz(user?.timezone ?? "UTC");
  }, [user]);

  const update = useMutation({
    mutationFn: () => api.updateMe({ full_name: fullName, timezone: tz }),
    onSuccess: (u) => {
      setUser(u);
      toast.success("Profile updated");
    },
    onError: () => toast.error("Update failed"),
  });

  const devices = useQuery({ queryKey: ["devices"], queryFn: () => api.devices() });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">Manage your profile and connected devices.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Update your account information.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:max-w-md">
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input id="email" value={user?.email ?? ""} disabled />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="full_name">Full name</Label>
            <Input id="full_name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="timezone">Timezone</Label>
            <Input id="timezone" value={tz} onChange={(e) => setTz(e.target.value)} />
          </div>
          <Button onClick={() => update.mutate()} disabled={update.isPending} className="w-fit">
            {update.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            Save changes
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Connected devices</CardTitle>
          <CardDescription>Machines that have synced tracking data.</CardDescription>
        </CardHeader>
        <CardContent>
          {devices.isLoading ? (
            <div className="space-y-2">
              {[...Array(2)].map((_, i) => <Skeleton key={i} className="h-14" />)}
            </div>
          ) : (devices.data ?? []).length === 0 ? (
            <div className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
              <Monitor className="mx-auto mb-2 h-6 w-6 opacity-60" />
              No devices yet. Run the desktop agent to register one.
            </div>
          ) : (
            <ul className="divide-y divide-border">
              {devices.data!.map((d) => (
                <li key={d.id} className="flex items-center justify-between py-3 text-sm">
                  <div>
                    <div className="font-medium">{d.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {d.platform} · {d.hostname ?? "unknown host"} · agent {d.agent_version ?? "—"}
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {d.last_seen_at
                      ? `last seen ${format(parseISO(d.last_seen_at), "MMM d, HH:mm")}`
                      : "never seen"}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
