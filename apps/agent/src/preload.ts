/**
 * Preload script for the sign-in window.
 *
 * Exposes a tiny, well-defined surface (`window.ptaa`) to the renderer.
 * Renderer never gets `require`/Node access — preserves contextIsolation.
 */
import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("ptaa", {
  getConfig: (): Promise<{ apiUrl: string; signedIn: boolean }> =>
    ipcRenderer.invoke("ptaa:get-config"),
  setApiUrl: (url: string): Promise<boolean> =>
    ipcRenderer.invoke("ptaa:set-api-url", url),
  login: (email: string, password: string): Promise<{ ok: boolean; error?: string; user?: { email: string } }> =>
    ipcRenderer.invoke("ptaa:login", email, password),
});
