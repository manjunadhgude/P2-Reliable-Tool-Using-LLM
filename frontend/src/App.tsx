import { useCallback, useEffect, useMemo, useState } from 'react';
import { Activity, ArrowDownToLine, Check, ChevronDown, CircleHelp, ClipboardList, Clock3, Database, FileCheck2, Gauge, LoaderCircle, LogOut, MessageSquare, Plus, Send, ShieldCheck, Sparkles, X } from 'lucide-react';
import { API, Conversation, Message, Pending, request, User } from './api';

type Info = { backend_type: string; backend_label: string; model_id: string; model_revision?: string; synthetic_data: boolean; external_actions: boolean };
type Execution = { execution_id: string; tool_name: string; status: string; result: Record<string, unknown>; duration_ms: number };
type TurnResult = { turn_id: string; status: string; assistant_message: string; tool_executions: Execution[]; pending_action?: Pending };

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('p2_token') || '');
  const [user, setUser] = useState<User | null>(null);
  const [role, setRole] = useState('agent');
  const [info, setInfo] = useState<Info | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [active, setActive] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [pending, setPending] = useState<Pending[]>([]);
  const [benchmarks, setBenchmarks] = useState<any[]>([]);
  const [experiments, setExperiments] = useState<any[]>([]);
  const [composer, setComposer] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [trace, setTrace] = useState<any | null>(null);
  const [lastTurnId, setLastTurnId] = useState('');
  const [view, setView] = useState<'assistant' | 'review' | 'benchmarks' | 'experiments' | 'health'>('assistant');

  const signIn = useCallback(async (username: string) => {
    setLoading(true); setError('');
    try {
      const result = await request<{ access_token: string; user: User }>('/api/v1/auth/demo-session', undefined, { method: 'POST', body: JSON.stringify({ username }) });
      localStorage.setItem('p2_token', result.access_token); setToken(result.access_token); setUser(result.user); setRole(username);
    } catch (e) { setError((e as Error).message); } finally { setLoading(false); }
  }, []);

  const refresh = useCallback(async (auth = token) => {
    if (!auth) return;
    const [me, conv, sys, runs] = await Promise.all([
      request<User & { tenant_id: string }>('/api/v1/auth/me', auth), request<Conversation[]>('/api/v1/conversations', auth), request<Info>('/api/v1/system/info'), request<any[]>('/api/v1/benchmarks', auth),
    ]);
    setUser(me); setConversations(conv); setInfo(sys); setBenchmarks(runs);
    if (me.role === 'evaluator' || me.role === 'admin') setExperiments(await request<any[]>('/api/v1/experiments', auth));
    else setExperiments([]);
    if (me.role === 'supervisor' || me.role === 'admin') setPending(await request<Pending[]>('/api/v1/pending-actions', auth));
    else setPending([]);
  }, [token]);

  useEffect(() => { if (token) refresh().catch(e => { setError(e.message); localStorage.removeItem('p2_token'); setToken(''); }); else request<Info>('/api/v1/system/info').then(setInfo).catch(() => {}); }, [token, refresh]);
  useEffect(() => { if (!token || !active) return; request<any>(`/api/v1/conversations/${active.id}`, token).then(r => setMessages(r.messages)).catch(e => setError(e.message)); }, [token, active]);

  const createConversation = async () => {
    if (!token) return;
    try { const c = await request<Conversation>('/api/v1/conversations', token, { method: 'POST', body: JSON.stringify({ title: 'Support conversation' }) }); setConversations(x => [c, ...x]); setActive(c); setMessages([]); setView('assistant'); }
    catch (e) { setError((e as Error).message); }
  };

  const send = async (text = composer) => {
    if (!token || !text.trim() || sending) return;
    setError(''); setSending(true);
    try {
      let conversation = active;
      if (!conversation) { conversation = await request<Conversation>('/api/v1/conversations', token, { method: 'POST', body: JSON.stringify({ title: text.slice(0, 64) }) }); setActive(conversation); setConversations(x => [conversation!, ...x]); }
      const temp: Message = { id: crypto.randomUUID(), role: 'user', content: text, created_at: new Date().toISOString() };
      setMessages(m => [...m, temp]); setComposer('');
      const result = await request<TurnResult>(`/api/v1/conversations/${conversation.id}/messages`, token, { method: 'POST', body: JSON.stringify({ content: text }) });
      setLastTurnId(result.turn_id);
      const assistant: Message = { id: crypto.randomUUID(), role: 'assistant', content: result.assistant_message, created_at: new Date().toISOString() };
      setMessages(m => [...m.filter(v => v.id !== temp.id), temp, assistant]);
      if (result.pending_action) setPending(p => [result.pending_action!, ...p.filter(x => x.id !== result.pending_action!.id)]);
      const newMessages = await request<any>(`/api/v1/conversations/${conversation.id}`, token); setMessages(newMessages.messages);
      await refresh();
    } catch (e) { setError((e as Error).message); } finally { setSending(false); }
  };

  const resolve = async (id: string, action: 'approve' | 'reject') => {
    try { const result = await request<{message?: string; status: string}>(`/api/v1/pending-actions/${id}/${action}`, token, { method: 'POST' }); setNotice(result.message || `Action ${result.status}.`); await refresh(); }
    catch (e) { setError((e as Error).message); }
  };
  const runBenchmark = async () => { setLoading(true); setError(''); try { await request('/api/v1/benchmarks', token, { method: 'POST' }); setBenchmarks(await request<any[]>('/api/v1/benchmarks', token)); setExperiments(await request<any[]>('/api/v1/experiments', token)); } catch (e) { setError((e as Error).message); } finally { setLoading(false); } };
  const openTrace = async (id: string) => { try { setTrace(await request(`/api/v1/turns/${id}/trace`, token)); } catch (e) { setError((e as Error).message); } };
  const exportRun = async (id: string) => { try { const res = await fetch(`${API}/api/v1/benchmarks/${id}/export?format=csv`, { headers: { Authorization: `Bearer ${token}` } }); if (!res.ok) throw new Error('Could not export this run.'); const blob = await res.blob(); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `${id}.csv`; a.click(); URL.revokeObjectURL(url); } catch (e) { setError((e as Error).message); } };
  const signOut = () => { localStorage.removeItem('p2_token'); setToken(''); setUser(null); setActive(null); setMessages([]); setPending([]); setBenchmarks([]); setLastTurnId(''); };
  const latestRun = useMemo(() => benchmarks[0], [benchmarks]);
  const backendLabel = info?.backend_type === 'ollama' ? `Ollama / ${info.model_id}` : info?.backend_label || 'Checking backend…';

  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><Sparkles size={18}/></div><div><strong>P2 Operations</strong><small>Reliable tool use</small></div></div>
      <div className="workspace-label">WORKSPACE <span className="demo-chip">DEMO</span></div>
      <button className={`nav-item ${view === 'assistant' ? 'selected' : ''}`} onClick={() => setView('assistant')}><MessageSquare size={17}/> Assistant</button>
      <button className={`nav-item ${view === 'review' ? 'selected' : ''}`} onClick={() => setView('review')}><FileCheck2 size={17}/> Action review {pending.filter(p => p.status === 'pending').length > 0 && <span className="count">{pending.filter(p => p.status === 'pending').length}</span>}</button>
      <button className={`nav-item ${view === 'benchmarks' ? 'selected' : ''}`} onClick={() => setView('benchmarks')}><Gauge size={17}/> Benchmark lab</button>
      <button className={`nav-item ${view === 'experiments' ? 'selected' : ''}`} onClick={() => setView('experiments')}><ClipboardList size={17}/> Experiment history</button>
      <button className={`nav-item ${view === 'health' ? 'selected' : ''}`} onClick={() => setView('health')}><Activity size={17}/> System status</button>
      <div className="history-label">RECENT CONVERSATIONS <button aria-label="New conversation" onClick={createConversation}><Plus size={16}/></button></div>
      <div className="history-list">{conversations.map(c => <button key={c.id} className={`history-item ${active?.id === c.id ? 'active' : ''}`} onClick={() => { setActive(c); setLastTurnId(''); setView('assistant'); }}><MessageSquare size={15}/><span>{c.title}</span></button>)}</div>
      <div className="sidebar-bottom">
        <div className="backend-mini"><span className="status-dot"/><span>{backendLabel}</span></div>
        {user ? <button className="profile" onClick={signOut}><div className="avatar">{user.display_name.split(' ').map(x => x[0]).slice(0,2).join('')}</div><div className="profile-copy"><b>{user.display_name}</b><small>{user.role.replace('_',' ')}</small></div><LogOut size={16}/></button> : <div className="login-box"><label htmlFor="role">Demo identity</label><div className="login-row"><select id="role" value={role} onChange={e => setRole(e.target.value)}><option value="agent">Support agent</option><option value="supervisor">Supervisor</option><option value="evaluator">Evaluator</option></select><button onClick={() => signIn(role)} disabled={loading}>{loading ? <LoaderCircle className="spin" size={16}/> : 'Sign in'}</button></div></div>}
      </div>
    </aside>
    <main className="main">
      <header className="topbar"><div className="breadcrumb">P2 <span>/</span> {view === 'assistant' ? 'Assistant' : view === 'review' ? 'Action review' : view === 'benchmarks' ? 'Benchmark lab' : view === 'experiments' ? 'Experiment history' : 'System status'}</div><div className="top-actions"><span className="data-label"><Database size={14}/> Synthetic data</span><span className="help-icon" title="Help"><CircleHelp size={17}/></span></div></header>
      {error && <div className="error-banner" role="alert"><X size={16}/>{error}<button onClick={() => setError('')} aria-label="Dismiss">×</button></div>}
      {notice && <div className="notice" role="status"><b>{notice}</b></div>}
      {view === 'assistant' && <section className="assistant-page">
        {!active && messages.length === 0 ? <div className="welcome"><div className="welcome-icon"><Sparkles size={25}/></div><div className="eyebrow">P2 · SYNTHETIC E-COMMERCE OPERATIONS</div><h1>How can I help<br/>with an order?</h1><p>Look up order facts, check return policy, estimate eligibility, or prepare a support ticket for approval.</p><div className="prompt-grid">
          {[['Track an order','Where is order ORD-10021?'],['Check a return','Can I return items from ORD-10022?'],['Estimate a refund','Estimate the refund for ORD-10022'],['Prepare a ticket','Open a support ticket for delayed delivery on ORD-10021']].map(([title, prompt]) => <button key={title} onClick={() => send(prompt)} disabled={!token}><b>{title}</b><span>{prompt}</span><ChevronDown size={16}/></button>)}
        </div></div> : <div className="chat-wrap"><div className="chat-head"><div><h1>{active?.title || 'Support conversation'}</h1><span>Tool-grounded answers · Supervisor approval required for tickets</span></div><div className="chat-actions">{lastTurnId && <button className="quiet-button" onClick={() => openTrace(lastTurnId)}><Activity size={15}/> View trace</button>}<button className="quiet-button" onClick={createConversation}><Plus size={16}/> New chat</button></div></div><div className="messages" aria-live="polite">{messages.map(m => <div className={`message-row ${m.role}`} key={m.id}><div className="message-avatar">{m.role === 'assistant' ? <Sparkles size={15}/> : user?.display_name.split(' ').map(x => x[0]).slice(0,2).join('')}</div><div className="message-content"><div className="message-author">{m.role === 'assistant' ? 'P2 Assistant' : user?.display_name}</div><div className="message-bubble">{m.content}</div></div></div>)}{sending && <div className="thinking"><LoaderCircle className="spin" size={15}/> Checking approved tools…</div>}</div><div className="composer-box"><textarea value={composer} onChange={e => setComposer(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }} placeholder={token ? 'Ask about an order…' : 'Sign in with a demo identity to start'} disabled={!token || sending} rows={2}/><div className="composer-footer"><span>Enter to send · Shift+Enter for a new line</span><button onClick={() => send()} disabled={!token || !composer.trim() || sending} aria-label="Send"><Send size={16}/></button></div></div></div>}
      </section>}

      {view === 'review' && <section className="content-page"><div className="page-heading"><div><div className="eyebrow">HUMAN APPROVAL GATE</div><h1>Action review</h1><p>Proposed tickets stay pending until a supervisor approves them.</p></div><span className="secure-badge"><ShieldCheck size={15}/> Server verified</span></div>{!user ? <Empty text="Sign in as a supervisor to review pending actions."/> : user.role !== 'supervisor' && user.role !== 'admin' ? <Empty text="This view is available to supervisor accounts."/> : pending.filter(p => p.status === 'pending').length === 0 ? <Empty text="No pending actions. New ticket proposals will appear here."/> : <div className="action-list">{pending.filter(p => p.status === 'pending').map(p => <article className="action-card" key={p.id}><div className="card-top"><span className="status-pill pending"><Clock3 size={13}/> Pending approval</span><small>{new Date(p.created_at).toLocaleString()}</small></div><h2>{String(p.arguments.summary || 'Support ticket')}</h2><p>{String(p.arguments.description || '')}</p><div className="details-grid"><div><small>Order</small><b>{String(p.arguments.order_id || 'Not linked')}</b></div><div><small>Issue type</small><b>{String(p.arguments.issue_type || '').replaceAll('_',' ')}</b></div><div><small>Priority</small><b>{String(p.arguments.priority || '').toUpperCase()}</b></div></div><div className="approval-note"><ShieldCheck size={16}/> Approval records your identity and creates one demo ticket. Repeated approvals are idempotent.</div><div className="card-actions"><button className="reject-button" onClick={() => resolve(p.id,'reject')}><X size={15}/> Reject</button><button className="approve-button" onClick={() => resolve(p.id,'approve')}><Check size={16}/> Approve and create ticket</button></div></article>)}</div>}</section>}

      {view === 'benchmarks' && <section className="content-page"><div className="page-heading"><div><div className="eyebrow">MEASURED RUNS ONLY</div><h1>Benchmark lab</h1><p>Results are calculated from the saved synthetic validation split. The fixture backend is not an LLM.</p></div><button className="primary-button" onClick={runBenchmark} disabled={!user || user.role !== 'evaluator' || loading}>{loading ? <LoaderCircle className="spin" size={16}/> : <Gauge size={16}/>} Run validation benchmark</button></div>{!user ? <Empty text="Sign in as evaluator to start a run."/> : user.role !== 'evaluator' && user.role !== 'admin' ? <Empty text="Benchmark runs require the evaluator role."/> : <><div className="metric-row"><Metric label="Saved runs" value={String(benchmarks.length)}/><Metric label="Latest backend" value={latestRun?.backend || 'No runs yet'}/><Metric label="Latest split" value={latestRun?.split || '—'}/></div><div className="run-list">{benchmarks.map(run => <article className="run-card" key={run.id}><div className="run-icon"><Gauge size={17}/></div><div className="run-main"><b>{run.backend === 'deterministic_test' ? 'Deterministic test backend' : run.backend}</b><span>{run.dataset_version} · {run.split} · {new Date(run.started_at).toLocaleString()}</span><small>{run.metrics?.provenance || 'Metrics from persisted run artifact.'}</small></div><div className="run-score"><b>{run.metrics?.action_match_count ?? '—'} / {run.metrics?.denominator ?? 0}</b><span>action matches</span></div><button className="icon-link" onClick={() => exportRun(run.id)} aria-label="Export CSV"><ArrowDownToLine size={16}/></button></article>)}</div></>}</section>}

      {view === 'experiments' && <section className="content-page"><div className="page-heading"><div><div className="eyebrow">SAVED RUN RECORDS</div><h1>Experiment history</h1><p>Persisted benchmark runs and result artifacts. Fixture results are identified as simulated behavior.</p></div></div>{!user ? <Empty text="Sign in as evaluator to inspect experiment history."/> : user.role !== 'evaluator' && user.role !== 'admin' ? <Empty text="Experiment history requires the evaluator role."/> : experiments.length === 0 ? <Empty text="No saved experiments yet. Run a validation benchmark to add history."/> : <div className="run-list">{experiments.map(run => <article className="run-card" key={run.id}><div className="run-icon"><ClipboardList size={17}/></div><div className="run-main"><b>{run.name}</b><span>{run.backend} · {run.dataset_version} · {run.split} · {run.status}</span><small>{run.metrics?.provenance || `${run.metrics?.action_match_count ?? '—'} / ${run.metrics?.denominator ?? '—'} action matches · ${run.source}`}</small></div></article>)}</div>}</section>}

      {view === 'health' && <section className="content-page"><div className="page-heading"><div><div className="eyebrow">SERVICE CONFIGURATION</div><h1>System status</h1><p>Safe runtime information. Demo fixtures never represent real customer records.</p></div></div><div className="health-grid"><div className="health-card"><div className="health-icon"><Activity size={18}/></div><small>Active backend</small><b>{backendLabel}</b><p>{info?.backend_type === 'deterministic_test' ? 'Rule-based fixtures for demo flow and CI. Not an LLM.' : info?.backend_type === 'ollama' ? 'Local Ollama open-weight model; controller and server enforce workflow and permission rules.' : 'Transformers open-weight model adapter.'}</p></div><div className="health-card"><div className="health-icon"><Database size={18}/></div><small>Database</small><b>Persistent local relational store</b><p>Seeded synthetic tenant and order records.</p></div><div className="health-card"><div className="health-icon"><ShieldCheck size={18}/></div><small>Write safety</small><b>Supervisor approval required</b><p>Ticket writes use an idempotency key and server-side authorization.</p></div><div className="health-card"><div className="health-icon"><ClipboardList size={18}/></div><small>Model identity</small><b>{info?.model_id || '—'}</b><p>Revision: {info?.model_revision || 'n/a for fixture backend'}</p></div></div><div className="notice"><b>Scope guard</b><p>This project uses synthetic e-commerce data only. It cannot issue a refund, send an email, or contact an external service.</p></div></section>}
      <footer className="footer"><span>Applied AI · Reliable tool use</span><span>Local demo environment</span></footer>
    </main>
    {trace && <div className="modal-backdrop" onClick={() => setTrace(null)}><section className="trace-modal" onClick={e => e.stopPropagation()}><div className="modal-title"><div><div className="eyebrow">EXECUTION TRACE</div><h2>Tool activity</h2></div><button onClick={() => setTrace(null)} aria-label="Close"><X/></button></div><p className="trace-turn">Trace ID {trace.turn_id} · {trace.status}</p>{trace.controller_events?.map((event: any, index: number) => <div className="trace-event" key={`controller-${index}`}><b>Structured action and policy</b><span>{event.backend} · {event.model_id} · {event.controller_version || 'model path'}</span><pre>{JSON.stringify({proposal_action_type: event.proposal_action_type, proposal_tool_name: event.proposal_tool_name, proposal_arguments: event.proposal_arguments, final_action_type: event.final_action_type, final_tool_name: event.final_tool_name, decision: event.decision, outcome: event.outcome, reason: event.reason, model_calls: event.model_calls, controller_duration_ms: event.controller_duration_ms}, null, 2)}</pre></div>)}{trace.events?.length ? trace.events.map((event: any) => <div className="trace-event" key={event.execution_id}><b>{event.tool_name}</b><span>Validation {event.validation} · Authorization {event.authorization} · {event.duration_ms} ms</span><pre>{JSON.stringify({arguments: event.arguments, result: event.result},null,2)}</pre></div>) : <Empty text="No tool calls were recorded for this turn."/>}</section></div>}
  </div>;
}

function Empty({text}:{text:string}) { return <div className="empty-state"><div><ClipboardList size={19}/></div><p>{text}</p></div>; }
function Metric({label,value}:{label:string;value:string}) { return <div className="metric-card"><small>{label}</small><b>{value}</b></div>; }
