export const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export type User = { id: string; username: string; display_name: string; role: string };
export type Conversation = { id: string; title: string; created_at: string };
export type Message = { id: string; role: string; content: string; created_at: string };
export type Pending = { id: string; status: string; tool_name: string; arguments: Record<string, unknown>; created_at: string; ticket_id?: string };

export async function request<T>(path: string, token?: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API}${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers } });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail?.message || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}
