/**
 * Electron main process — Pulse desktop tracking agent.
 *
 * UX: a tray-only app. Clicking the tray icon shows a small status menu;
 * there's no main window unless the user explicitly signs in. The agent
 * starts tracking on launch (after auth) and runs invisibly.
 */
import { app, Menu, Tray, BrowserWindow, dialog, nativeImage, ipcMain, shell } from "electron";
import path from "node:path";
import os from "node:os";
import { config } from "./config";
import { logger } from "./logger";
import { storage } from "./storage";
import { tracker } from "./tracker";
import { sync } from "./sync";
import { api } from "./api";

const AGENT_VERSION = "0.1.0";

let tray: Tray | null = null;
let signinWindow: BrowserWindow | null = null;

// ─── Helpers ────────────────────────────────────────────────────────────
function platformId(): string {
  return process.platform === "win32"
    ? "win32"
    : process.platform === "darwin"
      ? "darwin"
      : "linux";
}

async function ensureDeviceRegistered() {
  if (!config.get("accessToken")) return; // not signed in yet
  if (config.get("deviceId")) return;

  try {
    const dev = await api.registerDevice({
      name: config.get("deviceName") || os.hostname(),
      platform: platformId(),
      hostname: os.hostname(),
      agent_version: AGENT_VERSION,
    });
    config.set("deviceId", dev.id);
    logger.info("device.registered", { id: dev.id });
  } catch (err) {
    logger.warn("device.register_failed", err);
  }
}

function updateTrayMenu() {
  if (!tray) return;
  const signedIn = !!config.get("accessToken");
  const pendingCount = storage.count();

  const menu = Menu.buildFromTemplate([
    {
      label: signedIn ? "Pulse · tracking" : "Pulse · not signed in",
      enabled: false,
    },
    { type: "separator" },
    {
      label: `Pending events: ${pendingCount}`,
      enabled: false,
    },
    {
      label: "Flush now",
      click: async () => {
        const r = await sync.flushNow();
        logger.info("manual.flush", r);
        updateTrayMenu();
      },
    },
    { type: "separator" },
    signedIn
      ? {
          label: "Sign out",
          click: () => {
            config.set("accessToken", null);
            config.set("refreshToken", null);
            config.set("deviceId", null);
            tracker.stop();
            sync.stop();
            updateTrayMenu();
            logger.info("user.signed_out");
          },
        }
      : {
          label: "Sign in…",
          click: () => openSignInWindow(),
        },
    {
      label: "Open dashboard",
      click: () => {
        const url = config.get("apiUrl").replace(/\/?$/, "").replace(":8000", ":3000");
        void shell.openExternal(url);
      },
    },
    { type: "separator" },
    {
      label: "Quit",
      click: () => {
        app.quit();
      },
    },
  ]);
  tray.setToolTip(signedIn ? "Pulse · tracking" : "Pulse · idle");
  tray.setContextMenu(menu);
}

function openSignInWindow() {
  if (signinWindow) {
    signinWindow.focus();
    return;
  }
  signinWindow = new BrowserWindow({
    width: 380,
    height: 460,
    resizable: false,
    fullscreenable: false,
    title: "Sign in to Pulse",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  signinWindow.removeMenu();
  void signinWindow.loadFile(path.join(__dirname, "..", "src", "ui", "signin.html"));
  signinWindow.on("closed", () => {
    signinWindow = null;
  });
}

// ─── IPC handlers (used by the sign-in window) ──────────────────────────
ipcMain.handle("ptaa:get-config", () => ({
  apiUrl: config.get("apiUrl"),
  signedIn: !!config.get("accessToken"),
}));

ipcMain.handle("ptaa:set-api-url", (_e, url: string) => {
  config.set("apiUrl", url);
  return true;
});

ipcMain.handle("ptaa:login", async (_e, email: string, password: string) => {
  try {
    const res = await api.login(email, password);
    await ensureDeviceRegistered();
    tracker.start();
    sync.start();
    updateTrayMenu();
    if (signinWindow) signinWindow.close();
    return { ok: true, user: res.user };
  } catch (err) {
    return { ok: false, error: (err as Error).message };
  }
});

// ─── App lifecycle ──────────────────────────────────────────────────────
function createTray() {
  // 16x16 transparent placeholder; users can replace with branded asset.
  const icon = nativeImage.createEmpty();
  tray = new Tray(icon);
  tray.setTitle("●"); // visible glyph on macOS menubar
  updateTrayMenu();

  // Refresh the menu count periodically so the user can see buffer drain.
  setInterval(updateTrayMenu, 10_000);
}

app.on("ready", async () => {
  // macOS: don't show in dock; we're a tray-only app.
  if (process.platform === "darwin" && app.dock) {
    app.dock.hide();
  }

  createTray();

  if (config.get("accessToken")) {
    await ensureDeviceRegistered();
    tracker.start();
    sync.start();
  } else {
    // Auto-prompt sign-in on first run.
    setTimeout(() => openSignInWindow(), 500);
  }
});

app.on("window-all-closed", (e: Event) => {
  // Keep the agent running even when no windows are open.
  e.preventDefault();
});

app.on("before-quit", () => {
  tracker.stop();
  sync.stop();
  storage.close();
});

process.on("uncaughtException", (err) => {
  logger.error("uncaught_exception", { message: err.message, stack: err.stack });
});

process.on("unhandledRejection", (reason) => {
  logger.error("unhandled_rejection", { reason: String(reason) });
});

// Single-instance lock — prevents two agents racing on the same SQLite db.
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
}
