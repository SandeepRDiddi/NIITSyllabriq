import { FormEvent, useEffect, useState } from "react";
import "./styles.css";

type User = {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
};

type Requirement = {
  id: number;
  customer_name: string;
  title: string;
  source_filename: string;
  created_by: string;
  created_at: string;
};

type DesignSummary = {
  id: number;
  requirement_id: number;
  title: string;
  created_by: string;
  status: string;
  similarity_score: number;
  created_at: string;
};

type ReviewTask = {
  id: number;
  design_document_id: number;
  reviewer_name: string;
  review_type: string;
  assigned_by?: string | null;
  status: string;
  comments?: string | null;
};

type TrainingDocument = {
  id: number;
  title: string;
  source_filename: string;
  uploaded_by: string;
  status: string;
  summary: string;
  created_at: string;
};

type WorkflowEvent = {
  id: number;
  event_type: string;
  entity_type: string;
  entity_id: number;
  actor_email: string;
  status: string;
  details: Record<string, unknown>;
  created_at: string;
};

type ReportSummary = {
  requirements_count: number;
  designs_count: number;
  training_documents_count: number;
  primary_pending_count: number;
  final_pending_count: number;
  final_approved_count: number;
  average_design_score: number;
  recent_events: WorkflowEvent[];
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

type Tab = "training" | "requirements" | "designs" | "reviews" | "reports";

function statusBadge(status: string) {
  const map: Record<string, string> = {
    PENDING: "badge badge-pending",
    APPROVED: "badge badge-approved",
    REJECTED: "badge badge-rejected",
    UNDER_PRIMARY_REVIEW: "badge badge-review",
    UNDER_FINAL_REVIEW: "badge badge-review",
    FINAL_APPROVED: "badge badge-final",
    PRIMARY_REJECTED: "badge badge-rejected",
    FINAL_REWORK_REQUIRED: "badge badge-rework",
    ACTIVE: "badge badge-approved",
  };
  return <span className={map[status] || "badge badge-default"}>{status.replace(/_/g, " ")}</span>;
}

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [user, setUser] = useState<User | null>(null);
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [designs, setDesigns] = useState<DesignSummary[]>([]);
  const [reviews, setReviews] = useState<ReviewTask[]>([]);
  const [trainingDocuments, setTrainingDocuments] = useState<TrainingDocument[]>([]);
  const [reportSummary, setReportSummary] = useState<ReportSummary | null>(null);
  const [loginForm, setLoginForm] = useState({ email: "admin@niit.com", password: "Admin@123" });
  // Requirements come in via email or call — no file upload needed
  const [reqForm, setReqForm] = useState({
    customerName: "",
    title: "",
    totalDurationHours: "",
    source: "email",
    rawText: "",
  });
  const [trainingForm, setTrainingForm] = useState({ title: "", file: null as File | null });
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" | "info" } | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("requirements");
  const [loading, setLoading] = useState(false);

  async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        ...(options.headers || {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail);
    }
    const ct = response.headers.get("content-type") || "";
    if (ct.includes("application/json")) return response.json() as Promise<T>;
    return {} as T;
  }

  function notify(text: string, type: "success" | "error" | "info" = "success") {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 5000);
  }

  useEffect(() => {
    if (!token) { setUser(null); return; }
    localStorage.setItem("token", token);
    void refreshDashboard();
  }, [token]);

  async function refreshDashboard() {
    try {
      const me = await api<User>("/auth/me");
      setUser(me);
      const [reqs, dsns, tdocs] = await Promise.all([
        api<Requirement[]>("/requirements"),
        api<DesignSummary[]>("/designs"),
        api<TrainingDocument[]>("/training"),
      ]);
      setRequirements(reqs);
      setDesigns(dsns);
      setTrainingDocuments(tdocs);
      if (["admin", "primary_reviewer", "final_reviewer"].includes(me.role)) {
        setReviews(await api<ReviewTask[]>("/reviews"));
      } else {
        setReviews([]);
      }
      if (me.role === "admin") {
        setReportSummary(await api<ReportSummary>("/reports/summary"));
      }
    } catch {
      setToken("");
    }
  }

  async function handleLogin(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api<{ access_token: string }>("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(loginForm),
      });
      setToken(res.access_token);
    } catch (err) {
      notify(`Login failed: ${err instanceof Error ? err.message : String(err)}`, "error");
    } finally {
      setLoading(false);
    }
  }

  // Save the requirement from typed/pasted text (email, call notes, etc.)
  async function handleSaveRequirement(e: FormEvent, andGenerate = false) {
    e.preventDefault();
    if (!reqForm.customerName.trim() || !reqForm.title.trim() || !reqForm.rawText.trim()) {
      notify("Please fill in Customer Name, Program Title and the requirement text.", "error");
      return;
    }
    setLoading(true);
    try {
      const body: Record<string, unknown> = {
        customer_name: reqForm.customerName.trim(),
        title: reqForm.title.trim(),
        raw_text: reqForm.rawText.trim(),
        source: reqForm.source,
      };
      if (reqForm.totalDurationHours) {
        body.total_duration_hours = parseInt(reqForm.totalDurationHours, 10);
      }
      const created = await api<{ id: number }>("/requirements/text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      notify(andGenerate ? "Requirement saved — generating design now…" : "Requirement saved successfully.", "success");
      setReqForm({ customerName: "", title: "", totalDurationHours: "", source: "email", rawText: "" });
      await refreshDashboard();
      if (andGenerate) {
        // Immediately trigger design generation for the just-created requirement
        await api(`/designs/generate/${created.id}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ requested_by: user?.email || "system" }),
        });
        notify("Design generated and sent to primary reviewer.");
        setActiveTab("designs");
        await refreshDashboard();
      }
    } catch (err) {
      notify(`Failed: ${err instanceof Error ? err.message : String(err)}`, "error");
    } finally {
      setLoading(false);
    }
  }

  async function handleTrainingUpload(e: FormEvent) {
    e.preventDefault();
    if (!trainingForm.file) return;
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append("file", trainingForm.file);
      await api(`/training/upload?title=${encodeURIComponent(trainingForm.title)}`, { method: "POST", body: fd });
      notify("Training document processed and added to library.");
      setTrainingForm({ title: "", file: null });
      await refreshDashboard();
    } catch (err) {
      notify(`Training upload failed: ${err instanceof Error ? err.message : String(err)}`, "error");
    } finally {
      setLoading(false);
    }
  }

  async function generateDesign(requirementId: number) {
    setLoading(true);
    try {
      await api(`/designs/generate/${requirementId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ requested_by: user?.email || "system" }),
      });
      notify("Design generated and submitted for primary review.");
      setActiveTab("designs");
      await refreshDashboard();
    } catch (err) {
      notify(`Generation failed: ${err instanceof Error ? err.message : String(err)}`, "error");
    } finally {
      setLoading(false);
    }
  }

  async function submitReview(taskId: number, decision: "approve" | "reject") {
    setLoading(true);
    try {
      await api(`/reviews/${taskId}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reviewer_name: user?.email, decision, comments: `${decision}d via portal` }),
      });
      notify(`Review ${decision}d successfully.`);
      await refreshDashboard();
    } catch (err) {
      notify(`Review failed: ${err instanceof Error ? err.message : String(err)}`, "error");
    } finally {
      setLoading(false);
    }
  }

  async function exportDesign(designId: number, fileFormat: "md" | "docx" | "pdf") {
    try {
      const res = await fetch(`${API_BASE}/designs/${designId}/export?version=final&file_format=${fileFormat}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `design-${designId}.${fileFormat}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      notify(`Export failed: ${err instanceof Error ? err.message : String(err)}`, "error");
    }
  }

  // ── Login page ──────────────────────────────────────────────────────────────
  if (!token || !user) {
    return (
      <div className="login-shell">
        <div className="login-card">
          <div className="login-logo">NIIT</div>
          <h1>Design Automation</h1>
          <p>Enterprise design generation, review &amp; export workflow.</p>
          {message && <div className={`alert alert-${message.type}`}>{message.text}</div>}
          <form onSubmit={handleLogin} className="stack">
            <div className="field">
              <label>Email address</label>
              <input
                type="email"
                value={loginForm.email}
                onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                placeholder="you@niit.com"
              />
            </div>
            <div className="field">
              <label>Password</label>
              <input
                type="password"
                value={loginForm.password}
                onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                placeholder="••••••••"
              />
            </div>
            <button type="submit" disabled={loading} style={{ marginTop: 6 }}>
              {loading ? "Signing in…" : "Sign In"}
            </button>
          </form>
          <p className="hint" style={{ marginTop: 20 }}>
            Accounts: admin@niit.com &nbsp;|&nbsp; designer@niit.com &nbsp;|&nbsp; primary.reviewer@niit.com
          </p>
        </div>
      </div>
    );
  }

  const canEdit = user.role === "admin" || user.role === "designer";
  const canReview = ["admin", "primary_reviewer", "final_reviewer"].includes(user.role);
  const pendingReviews = reviews.filter((r) => r.status === "PENDING").length;

  const tabs: { id: Tab; label: string; badge?: number }[] = [
    { id: "requirements", label: "Requirements" },
    { id: "designs", label: "Designs" },
    ...(canEdit ? [{ id: "training" as Tab, label: "Training Library" }] : []),
    ...(canReview ? [{ id: "reviews" as Tab, label: "Reviews", badge: pendingReviews }] : []),
    ...(user.role === "admin" ? [{ id: "reports" as Tab, label: "Reports" }] : []),
  ];

  return (
    <div className="shell">
      {/* Topbar */}
      <header className="topbar">
        <div className="topbar-brand">
          <span className="topbar-logo">NIIT</span>
          <h1>Design Automation</h1>
        </div>
        <div className="topbar-user">
          <p>{user.full_name} &nbsp;·&nbsp; {user.role.replace(/_/g, " ")}</p>
          <button
            className="btn-ghost"
            style={{ color: "rgba(255,255,255,0.75)", border: "1px solid rgba(255,255,255,0.2)", padding: "6px 16px" }}
            onClick={() => { localStorage.removeItem("token"); setToken(""); }}
          >
            Sign Out
          </button>
        </div>
      </header>

      {/* Tabs */}
      <nav className="tabs">
        {tabs.map((t) => (
          <button
            key={t.id}
            className={`tab${activeTab === t.id ? " active" : ""}`}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
            {t.badge ? (
              <span style={{ marginLeft: 6, background: "var(--red)", color: "white", borderRadius: 10, padding: "1px 7px", fontSize: 11 }}>
                {t.badge}
              </span>
            ) : null}
          </button>
        ))}
      </nav>

      <main className="content">
        {message && (
          <div className={`alert alert-${message.type}`}>
            {message.text}
          </div>
        )}

        {/* ── Requirements tab ─────────────────────── */}
        {activeTab === "requirements" && (
          <div>
            {canEdit && (
              <div className="panel" style={{ marginBottom: 24 }}>
                <p className="panel-title">New Program Requirement</p>
                <p className="hint" style={{ marginBottom: 16 }}>
                  Paste the requirement from an email, type notes from a discovery call, or enter anything the customer communicated.
                  No file needed — just type or paste the text below.
                </p>
                <form onSubmit={(e) => handleSaveRequirement(e, false)}>
                  {/* Row 1: Customer + Title */}
                  <div className="grid" style={{ marginBottom: 12 }}>
                    <div className="field">
                      <label>Customer / Organisation Name <span style={{ color: "var(--red)" }}>*</span></label>
                      <input
                        value={reqForm.customerName}
                        onChange={(e) => setReqForm({ ...reqForm, customerName: e.target.value })}
                        placeholder="e.g. Accenture, TCS, Internal"
                        required
                      />
                    </div>
                    <div className="field">
                      <label>Program Title <span style={{ color: "var(--red)" }}>*</span></label>
                      <input
                        value={reqForm.title}
                        onChange={(e) => setReqForm({ ...reqForm, title: e.target.value })}
                        placeholder="e.g. Cloud Native Development with AWS"
                        required
                      />
                    </div>
                  </div>

                  {/* Row 2: Duration + Source */}
                  <div className="grid" style={{ marginBottom: 12 }}>
                    <div className="field">
                      <label>Total Duration (hours)</label>
                      <input
                        type="number"
                        min="1"
                        value={reqForm.totalDurationHours}
                        onChange={(e) => setReqForm({ ...reqForm, totalDurationHours: e.target.value })}
                        placeholder="e.g. 40"
                      />
                    </div>
                    <div className="field">
                      <label>How did this requirement come in?</label>
                      <select
                        value={reqForm.source}
                        onChange={(e) => setReqForm({ ...reqForm, source: e.target.value })}
                        style={{ height: 38, borderRadius: 6, border: "1px solid var(--border)", padding: "0 10px", fontSize: 14 }}
                      >
                        <option value="email">Email</option>
                        <option value="call_notes">Call / Meeting Notes</option>
                        <option value="teams">Teams / Slack Message</option>
                        <option value="whatsapp">WhatsApp</option>
                        <option value="direct_entry">Directly typed</option>
                        <option value="other">Other</option>
                      </select>
                    </div>
                  </div>

                  {/* Requirement text area */}
                  <div className="field" style={{ marginBottom: 16 }}>
                    <label>Requirement Details <span style={{ color: "var(--red)" }}>*</span></label>
                    <textarea
                      value={reqForm.rawText}
                      onChange={(e) => setReqForm({ ...reqForm, rawText: e.target.value })}
                      rows={10}
                      placeholder={`Paste the email or type the requirement here.\n\nExample:\n"We need a 40-hour program on React and Node.js for a batch of 25 experienced Java developers at Infosys. The program should cover frontend fundamentals, hooks, REST API integration, and deployment to AWS. Pre-requisites are basic JavaScript and Git knowledge."`}
                      required
                      style={{ width: "100%", resize: "vertical", fontFamily: "inherit", fontSize: 14, padding: 10, borderRadius: 6, border: "1px solid var(--border)", lineHeight: 1.6 }}
                    />
                    <p className="hint" style={{ marginTop: 4 }}>
                      {reqForm.rawText.length > 0 ? `${reqForm.rawText.length} characters entered` : "Minimum 50 characters recommended for a good design output"}
                    </p>
                  </div>

                  {/* Action buttons */}
                  <div className="row" style={{ gap: 12 }}>
                    <button type="submit" className="btn-outline" disabled={loading} style={{ minWidth: 160 }}>
                      {loading ? "Saving…" : "Save Requirement"}
                    </button>
                    <button
                      type="button"
                      disabled={loading}
                      style={{ minWidth: 220, background: "var(--navy)", color: "white", border: "none", borderRadius: 6, padding: "8px 20px", cursor: "pointer", fontWeight: 600, fontSize: 14 }}
                      onClick={(e) => handleSaveRequirement(e as unknown as FormEvent, true)}
                    >
                      {loading ? "Working…" : "⚡ Save & Generate Design"}
                    </button>
                  </div>
                </form>
              </div>
            )}

            <div className="panel">
              <p className="panel-title">All Requirements ({requirements.length})</p>
              {requirements.length === 0 ? (
                <div className="empty">No requirements yet. Enter the first one above.</div>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Program Title</th>
                      <th>Customer</th>
                      <th>Source</th>
                      <th>Entered by</th>
                      {canEdit && <th>Action</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {requirements.map((r) => {
                      // Convert raw source filename to human-readable label
                      const srcRaw = r.source_filename || "";
                      const srcLabel = srcRaw.startsWith("email") ? "Email"
                        : srcRaw.startsWith("call") ? "Call Notes"
                        : srcRaw.startsWith("teams") ? "Teams / Slack"
                        : srcRaw.startsWith("whatsapp") ? "WhatsApp"
                        : srcRaw.startsWith("direct") ? "Direct Entry"
                        : "Other";
                      return (
                        <tr key={r.id}>
                          <td className="hint">{r.id}</td>
                          <td style={{ fontWeight: 600 }}>{r.title}</td>
                          <td>{r.customer_name}</td>
                          <td className="hint">{srcLabel}</td>
                          <td className="hint">{r.created_by}</td>
                          {canEdit && (
                            <td>
                              <button className="btn-sm" onClick={() => generateDesign(r.id)} disabled={loading}>
                                Generate Design
                              </button>
                            </td>
                          )}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* ── Designs tab ──────────────────────────── */}
        {activeTab === "designs" && (
          <div className="panel">
            <p className="panel-title">Generated Designs ({designs.length})</p>
            {designs.length === 0 ? (
              <div className="empty">No designs generated yet. Go to Requirements to generate one.</div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Title</th>
                    <th>Status</th>
                    <th>Similarity</th>
                    <th>Created by</th>
                    <th>Export</th>
                  </tr>
                </thead>
                <tbody>
                  {designs.map((d) => {
                    const score = d.similarity_score;
                    const barClass = score >= 0.78 ? "" : score >= 0.5 ? " mid" : " low";
                    return (
                      <tr key={d.id}>
                        <td className="hint">{d.id}</td>
                        <td style={{ fontWeight: 600 }}>{d.title}</td>
                        <td>{statusBadge(d.status)}</td>
                        <td>
                          <div className="row" style={{ gap: 8, alignItems: "center" }}>
                            <div className="score-bar-wrap" style={{ width: 80 }}>
                              <div className={`score-bar${barClass}`} style={{ width: `${Math.min(score * 100, 100)}%` }} />
                            </div>
                            <span className="hint">{(score * 100).toFixed(0)}%</span>
                          </div>
                        </td>
                        <td className="hint">{d.created_by}</td>
                        <td>
                          <div className="row" style={{ gap: 6 }}>
                            <button className="btn-sm btn-outline" onClick={() => exportDesign(d.id, "md")}>MD</button>
                            <button className="btn-sm btn-outline" onClick={() => exportDesign(d.id, "docx")}>DOCX</button>
                            <button className="btn-sm btn-outline" onClick={() => exportDesign(d.id, "pdf")}>PDF</button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* ── Training tab ─────────────────────────── */}
        {activeTab === "training" && canEdit && (
          <div>
            <div className="panel" style={{ marginBottom: 24 }}>
              <p className="panel-title">Add to Training Library</p>
              <p className="hint" style={{ marginBottom: 16 }}>
                Upload prior design documents (PDF, DOCX, TXT). The system will use the local LLM to extract structured knowledge for similarity matching and design generation.
              </p>
              <form onSubmit={handleTrainingUpload}>
                <div className="grid" style={{ marginBottom: 10 }}>
                  <div className="field">
                    <label>Document Title</label>
                    <input
                      value={trainingForm.title}
                      onChange={(e) => setTrainingForm({ ...trainingForm, title: e.target.value })}
                      placeholder="e.g. ERP Migration Reference Design"
                    />
                  </div>
                  <div className="field">
                    <label>File</label>
                    <input type="file" onChange={(e) => setTrainingForm({ ...trainingForm, file: e.target.files?.[0] || null })} />
                  </div>
                </div>
                <button type="submit" disabled={loading}>
                  {loading ? "Processing with LLM…" : "Upload & Train"}
                </button>
              </form>
            </div>

            <div className="panel">
              <p className="panel-title">Training Library ({trainingDocuments.length} documents)</p>
              {trainingDocuments.length === 0 ? (
                <div className="empty">No training documents yet.</div>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Title</th>
                      <th>File</th>
                      <th>Status</th>
                      <th>Summary</th>
                      <th>Uploaded by</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trainingDocuments.map((t) => (
                      <tr key={t.id}>
                        <td className="hint">{t.id}</td>
                        <td style={{ fontWeight: 600 }}>{t.title}</td>
                        <td className="hint">{t.source_filename}</td>
                        <td>{statusBadge(t.status || "ACTIVE")}</td>
                        <td className="hint" style={{ maxWidth: 300 }}>{t.summary?.slice(0, 120)}{t.summary?.length > 120 ? "…" : ""}</td>
                        <td className="hint">{t.uploaded_by}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* ── Reviews tab ──────────────────────────── */}
        {activeTab === "reviews" && canReview && (
          <div>
            {reviews.filter((r) => r.status === "PENDING").length > 0 && (
              <div className="alert alert-info" style={{ marginBottom: 20 }}>
                You have {reviews.filter((r) => r.status === "PENDING").length} pending review{reviews.filter((r) => r.status === "PENDING").length > 1 ? "s" : ""} awaiting action.
              </div>
            )}
            <div className="panel">
              <p className="panel-title">Review Tasks ({reviews.length})</p>
              {reviews.length === 0 ? (
                <div className="empty">No review tasks assigned to you.</div>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Task #</th>
                      <th>Design #</th>
                      <th>Review Type</th>
                      <th>Assigned by</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reviews.map((r) => (
                      <tr key={r.id}>
                        <td className="hint">{r.id}</td>
                        <td style={{ fontWeight: 600 }}>Design #{r.design_document_id}</td>
                        <td>
                          <span className="badge badge-review">{r.review_type} review</span>
                        </td>
                        <td className="hint">{r.assigned_by || "—"}</td>
                        <td>{statusBadge(r.status)}</td>
                        <td>
                          {r.status === "PENDING" ? (
                            <div className="row" style={{ gap: 6 }}>
                              <button className="btn-sm btn-success" onClick={() => submitReview(r.id, "approve")} disabled={loading}>
                                Approve
                              </button>
                              <button className="btn-sm btn-danger" onClick={() => submitReview(r.id, "reject")} disabled={loading}>
                                Reject
                              </button>
                            </div>
                          ) : (
                            <span className="hint">{r.comments || "—"}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* ── Reports tab ──────────────────────────── */}
        {activeTab === "reports" && reportSummary && (
          <div>
            <div className="grid-3" style={{ marginBottom: 24 }}>
              <div className="metric metric-accent">
                <span className="metric-value">{reportSummary.requirements_count}</span>
                <span className="metric-label">Requirements</span>
              </div>
              <div className="metric metric-accent">
                <span className="metric-value">{reportSummary.designs_count}</span>
                <span className="metric-label">Designs Generated</span>
              </div>
              <div className="metric metric-accent">
                <span className="metric-value">{reportSummary.final_approved_count}</span>
                <span className="metric-label">Final Approved</span>
              </div>
              <div className="metric metric-accent">
                <span className="metric-value">{reportSummary.training_documents_count}</span>
                <span className="metric-label">Training Docs</span>
              </div>
              <div className="metric metric-accent">
                <span className="metric-value">{reportSummary.primary_pending_count}</span>
                <span className="metric-label">Primary Pending</span>
              </div>
              <div className="metric metric-accent">
                <span className="metric-value">{(reportSummary.average_design_score * 100).toFixed(0)}%</span>
                <span className="metric-label">Avg Design Score</span>
              </div>
            </div>

            <div className="panel">
              <p className="panel-title">Recent Workflow Events</p>
              {reportSummary.recent_events.length === 0 ? (
                <div className="empty">No events recorded yet.</div>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Event</th>
                      <th>Entity</th>
                      <th>Actor</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportSummary.recent_events.map((e) => (
                      <tr key={e.id}>
                        <td className="hint">{e.id}</td>
                        <td style={{ fontWeight: 600 }}>{e.event_type.replace(/_/g, " ")}</td>
                        <td className="hint">{e.entity_type} #{e.entity_id}</td>
                        <td className="hint">{e.actor_email}</td>
                        <td>{statusBadge(e.status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
