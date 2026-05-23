"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, Send, Sparkles, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { formatDistanceToNow, parseISO } from "date-fns";

import { api } from "@/lib/api";
import type { ChatMessagePublic } from "@/lib/types";
import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const SUGGESTIONS = [
  "Why was my productivity low today?",
  "How much time did I spend coding this week?",
  "Which app distracted me most?",
  "What are my peak focus hours?",
  "Summarize my week.",
];

export default function ChatPage() {
  const qc = useQueryClient();
  const [activeId, setActiveId] = React.useState<string | null>(null);
  const [input, setInput] = React.useState("");

  const sessions = useQuery({ queryKey: ["chat", "sessions"], queryFn: () => api.chatSessions() });
  const detail = useQuery({
    queryKey: ["chat", "session", activeId],
    queryFn: () => api.chatSession(activeId!),
    enabled: !!activeId,
  });

  const send = useMutation({
    mutationFn: (msg: string) => api.sendChat({ session_id: activeId ?? undefined, message: msg }),
    onSuccess: (res) => {
      setActiveId(res.session.id);
      qc.invalidateQueries({ queryKey: ["chat", "sessions"] });
      qc.invalidateQueries({ queryKey: ["chat", "session", res.session.id] });
    },
    onError: () => toast.error("Failed to send message"),
  });

  const del = useMutation({
    mutationFn: (id: string) => api.deleteChat(id),
    onSuccess: () => {
      setActiveId(null);
      qc.invalidateQueries({ queryKey: ["chat", "sessions"] });
    },
  });

  const onSend = (msg?: string) => {
    const text = (msg ?? input).trim();
    if (!text || send.isPending) return;
    setInput("");
    send.mutate(text);
  };

  const visibleMessages: ChatMessagePublic[] = React.useMemo(() => {
    const persisted = detail.data?.messages ?? [];
    if (send.isPending) {
      const userPlaceholder: ChatMessagePublic = {
        id: "pending-user",
        role: "user",
        content: send.variables ?? "",
        created_at: new Date().toISOString(),
      };
      const assistantPlaceholder: ChatMessagePublic = {
        id: "pending-assistant",
        role: "assistant",
        content: "",
        created_at: new Date().toISOString(),
      };
      // Don't double up if last message already matches
      if (
        persisted.length === 0 ||
        persisted[persisted.length - 1].content !== send.variables
      ) {
        return [...persisted, userPlaceholder, assistantPlaceholder];
      }
      return [...persisted, assistantPlaceholder];
    }
    return persisted;
  }, [detail.data, send.isPending, send.variables]);

  return (
    <div className="grid h-[calc(100vh-7rem)] gap-4 lg:grid-cols-[260px_1fr]">
      {/* Sessions list */}
      <Card className="flex flex-col overflow-hidden">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <div className="text-sm font-semibold">Conversations</div>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setActiveId(null)}
            className="h-7 gap-1 px-2 text-xs"
          >
            New
          </Button>
        </div>
        <div className="scrollbar-thin flex-1 overflow-y-auto px-2 py-2">
          {sessions.isLoading ? (
            <div className="space-y-2 px-2">
              {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-10" />)}
            </div>
          ) : (sessions.data ?? []).length === 0 ? (
            <div className="px-2 py-3 text-xs text-muted-foreground">No conversations yet.</div>
          ) : (
            <ul className="space-y-1">
              {sessions.data!.map((s) => (
                <li key={s.id}>
                  <button
                    onClick={() => setActiveId(s.id)}
                    className={cn(
                      "group flex w-full items-center justify-between gap-2 rounded-md px-2.5 py-2 text-left text-sm transition-colors",
                      activeId === s.id
                        ? "bg-accent text-foreground"
                        : "text-muted-foreground hover:bg-accent/60 hover:text-foreground",
                    )}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="truncate font-medium">{s.title}</div>
                      <div className="text-[11px] text-muted-foreground">
                        {formatDistanceToNow(parseISO(s.updated_at), { addSuffix: true })}
                      </div>
                    </div>
                    <span
                      role="button"
                      tabIndex={0}
                      aria-label="Delete conversation"
                      className="opacity-0 transition-opacity hover:text-danger group-hover:opacity-100"
                      onClick={(e) => {
                        e.stopPropagation();
                        del.mutate(s.id);
                      }}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </Card>

      {/* Conversation */}
      <Card className="flex flex-col overflow-hidden">
        <div className="flex items-center gap-2 border-b border-border px-4 py-3">
          <div className="grid h-7 w-7 place-items-center rounded-md bg-primary/15 text-primary">
            <Sparkles className="h-3.5 w-3.5" />
          </div>
          <div className="text-sm font-semibold">
            {detail.data?.title ?? "Pulse · AI assistant"}
          </div>
        </div>

        <div className="scrollbar-thin flex-1 overflow-y-auto px-6 py-6">
          {!activeId && visibleMessages.length === 0 ? (
            <Welcome onPick={onSend} />
          ) : (
            <div className="mx-auto flex max-w-2xl flex-col gap-4">
              <AnimatePresence initial={false}>
                {visibleMessages.map((m) => (
                  <Message key={m.id} message={m} pending={m.id === "pending-assistant"} />
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>

        <div className="border-t border-border p-4">
          <div className="mx-auto flex max-w-2xl items-end gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask Pulse anything about your productivity…"
              rows={1}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  onSend();
                }
              }}
              className="scrollbar-thin max-h-32 min-h-[44px] flex-1 resize-none rounded-md border border-input bg-background px-3 py-2.5 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            <Button onClick={() => onSend()} disabled={send.isPending || !input.trim()} size="icon">
              {send.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

function Message({ message, pending }: { message: ChatMessagePublic; pending?: boolean }) {
  const isUser = message.role === "user";
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.18 }}
      className={cn("flex gap-2", isUser ? "justify-end" : "justify-start")}
    >
      {!isUser && (
        <div className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-primary/15 text-primary">
          <Sparkles className="h-3.5 w-3.5" />
        </div>
      )}
      <div
        className={cn(
          "max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
          isUser
            ? "rounded-tr-sm bg-primary text-primary-foreground shadow-sm"
            : "rounded-tl-sm border border-border bg-card",
        )}
      >
        {pending ? (
          <span className="inline-flex gap-1">
            <Dot delay={0} />
            <Dot delay={0.2} />
            <Dot delay={0.4} />
          </span>
        ) : (
          <div className="whitespace-pre-line">{message.content}</div>
        )}
      </div>
    </motion.div>
  );
}

function Dot({ delay }: { delay: number }) {
  return (
    <motion.span
      animate={{ opacity: [0.3, 1, 0.3], y: [0, -2, 0] }}
      transition={{ duration: 1.2, repeat: Infinity, delay }}
      className="inline-block h-1.5 w-1.5 rounded-full bg-current"
    />
  );
}

function Welcome({ onPick }: { onPick: (q: string) => void }) {
  return (
    <div className="mx-auto flex max-w-xl flex-col items-center justify-center gap-6 py-12 text-center">
      <div className="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-brand-400 to-brand-700 shadow-lg shadow-primary/30">
        <Sparkles className="h-5 w-5 text-white" />
      </div>
      <div className="space-y-2">
        <h2 className="text-xl font-semibold">Ask Pulse anything</h2>
        <p className="text-sm text-muted-foreground">
          The assistant has access to your last 7 days of activity. Try one of these:
        </p>
      </div>
      <div className="flex flex-wrap justify-center gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onPick(s)}
            className="rounded-full border border-border bg-card px-3 py-1.5 text-xs transition-colors hover:border-primary/40 hover:bg-accent"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
