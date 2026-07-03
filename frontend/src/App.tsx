import { FormEvent, useEffect, useState } from "react";
import "./styles.css";
import DiscoveryQuestionnaire, { DiscoveryAnswers, EMPTY_DISCOVERY_ANSWERS } from "./DiscoveryQuestionnaire";

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

type DesignReference = {
  source_requirement_id: number;
  source_design_id?: number | null;
  source_training_document_id?: number | null;
  source_type: string;
  source_title: string;
  similarity_score: number;
  reused_sections: string[];
};

type DesignScorecard = {
  requirement_coverage_score: number;
  template_completeness_score: number;
  technical_consistency_score: number;
  reuse_relevance_score: number;
  risk_quality_score: number;
  review_readiness_score: number;
  llm_evaluation_score: number;
  overall_score: number;
  missing_requirements: string[];
  contradictions: string[];
  notes: string;
};

type DesignDetail = DesignSummary & {
  reused_content: boolean;
  draft_content: string;
  final_content?: string | null;
  traceability_map: Record<string, unknown>;
  references: DesignReference[];
  scorecard?: DesignScorecard | null;
  updated_at: string;
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
  chunk_count: number;
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

type LeadershipSummary = {
  total_users: number;
  active_users_count: number;
  active_tool_users_count: number;
  requirements_count: number;
  designs_generated_count: number;
  final_approved_count: number;
  rejected_or_rework_count: number;
  pending_review_count: number;
  pdf_exports_count: number;
  success_rate: number;
  average_design_score: number;
  recent_events: WorkflowEvent[];
};

type LLMUsageEvent = {
  id: number;
  provider: string;
  model: string;
  user_email: string;
  entity_type: string;
  entity_id: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost: number;
  created_at: string;
};

type LLMUsageByUser = {
  user_email: string;
  calls_count: number;
  total_tokens: number;
  estimated_cost: number;
};

type LLMUsageSummary = {
  total_calls: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost: number;
  by_user: LLMUsageByUser[];
  recent_events: LLMUsageEvent[];
};

type LLMProviderConfig = {
  id: number;
  provider: string;
  model: string;
  base_url: string;
  is_active: boolean;
  has_api_key: boolean;
  updated_by: string;
  updated_at: string;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

type Tab = "dashboard" | "training" | "requirements" | "designs" | "reviews" | "leaderboard" | "usage" | "reports" | "users" | "llm-config";

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

function scoreFraction(score: number) {
  return score > 1 ? score / 100 : score;
}

function scoreBarClass(score: number) {
  const normalized = scoreFraction(score);
  return normalized >= 0.78 ? "" : normalized >= 0.5 ? " mid" : " low";
}

function formatPercent(score: number) {
  return `${Math.round(scoreFraction(score) * 100)}%`;
}

function percentWidth(score: number) {
  return `${Math.min(scoreFraction(score) * 100, 100)}%`;
}

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [user, setUser] = useState<User | null>(null);
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [designs, setDesigns] = useState<DesignSummary[]>([]);
  const [reviews, setReviews] = useState<ReviewTask[]>([]);
  const [trainingDocuments, setTrainingDocuments] = useState<TrainingDocument[]>([]);
  const [reportSummary, setReportSummary] = useState<ReportSummary | null>(null);
  const [leadershipSummary, setLeadershipSummary] = useState<LeadershipSummary | null>(null);
  const [usageSummary, setUsageSummary] = useState<LLMUsageSummary | null>(null);
  const [llmConfig, setLlmConfig] = useState<LLMProviderConfig | null>(null);
  const [llmForm, setLlmForm] = useState({ provider: "ollama", model: "qwen2.5:7b-instruct", base_url: "http://localhost:11434", api_key: "" });
  const [loginForm, setLoginForm] = useState({ email: "admin@niit.com", password: "Admin@123" });
  // Requirements come in via email or call — no file upload needed
  const [reqForm, setReqForm] = useState({
    customerName: "",
    title: "",
    totalDurationHours: "",
    source: "email",
    rawText: "",
    file: null as File | null,
    discovery: EMPTY_DISCOVERY_ANSWERS,
  });
  const [trainingForm, setTrainingForm] = useState({ title: "", file: null as File | null });
  const [selectedDesign, setSelectedDesign] = useState<DesignDetail | null>(null);
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" | "info" } | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");
  const [clearing, setClearing] = useState(false);
  const [loading, setLoading] = useState(false);

  // User management
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [userForm, setUserForm] = useState({ email: "", full_name: "", role: "primary_reviewer", password: "" });

  // Reviewer picker — shown as inline modal before generation
  const [reviewerPick, setReviewerPick] = useState<{
    reqId: number | null;
    reqTitle: string;
    selectedReviewers: string[];
    andGenerate: boolean;
  }>({ reqId: null, reqTitle: "", selectedReviewers: [], andGenerate: false });

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
        const [summary, users, activeLlm] = await Promise.all([
          api<ReportSummary>("/reports/summary"),
          api<User[]>("/users"),
          api<LLMProviderConfig>("/admin/llm-config"),
        ]);
        setReportSummary(summary);
        setAllUsers(users);
        setLlmConfig(activeLlm);
        setLlmForm({
          provider: activeLlm.provider,
          model: activeLlm.model,
          base_url: activeLlm.base_url,
          api_key: "",
        });
      } else {
        setLlmConfig(null);
      }
      if (["admin", "leadership", "svp", "executive"].includes(me.role)) {
        const [leadership, usage] = await Promise.all([
          api<LeadershipSummary>("/reports/leadership"),
          api<LLMUsageSummary>("/reports/usage"),
        ]);
        setLeadershipSummary(leadership);
        setUsageSummary(usage);
      } else {
        setLeadershipSummary(null);
        setUsageSummary(null);
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
    if (!reqForm.customerName.trim() || !reqForm.title.trim()) {
      notify("Please fill in Customer Name and Program Title.", "error");
      return;
    }
    if (!reqForm.rawText.trim() && !reqForm.file) {
      notify("Paste requirement text or upload a requirement file.", "error");
      return;
    }
    setLoading(true);
    try {
      let created: { id: number };
      if (reqForm.file) {
        const fd = new FormData();
        fd.append("file", reqForm.file);
        created = await api<{ id: number }>(
          `/requirements/upload?customer_name=${encodeURIComponent(reqForm.customerName.trim())}&title=${encodeURIComponent(reqForm.title.trim())}`,
          { method: "POST", body: fd },
        );
      } else {
        const body: Record<string, unknown> = {
          customer_name: reqForm.customerName.trim(),
          title: reqForm.title.trim(),
          raw_text: reqForm.rawText.trim(),
          source: reqForm.source,
          discovery: {
            ...reqForm.discovery,
            learner_count: reqForm.discovery.learner_count ? parseInt(reqForm.discovery.learner_count, 10) : null,
          },
        };
        if (reqForm.totalDurationHours) {
          body.total_duration_hours = parseInt(reqForm.totalDurationHours, 10);
        }
        created = await api<{ id: number }>("/requirements/text", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
      }
      notify("Requirement saved successfully.");
      const savedTitle = reqForm.title.trim();
      setReqForm({ customerName: "", title: "", totalDurationHours: "", source: "email", rawText: "", file: null, discovery: EMPTY_DISCOVERY_ANSWERS });
      await refreshDashboard();
      if (andGenerate) {
        // Open reviewer picker for the just-created requirement
        const primaryUsers = allUsers.filter(u => ["primary_reviewer", "admin"].includes(u.role));
        const defaultReviewer = primaryUsers.length > 0 ? primaryUsers[0].email : "";
        setReviewerPick({
          reqId: created.id,
          reqTitle: savedTitle,
          selectedReviewers: defaultReviewer ? [defaultReviewer] : [],
          andGenerate: true,
        });
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

  async function createUser(e: FormEvent) {
    e.preventDefault();
    if (!userForm.email || !userForm.full_name || !userForm.password) {
      notify("Email, full name and password are required.", "error");
      return;
    }
    setLoading(true);
    try {
      await api("/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(userForm),
      });
      notify(`User ${userForm.email} created successfully.`);
      setUserForm({ email: "", full_name: "", role: "primary_reviewer", password: "" });
      await refreshDashboard();
    } catch (err) {
      notify(`Create user failed: ${err instanceof Error ? err.message : String(err)}`, "error");
    } finally {
      setLoading(false);
    }
  }

  async function saveLlmConfig(e: FormEvent) {
    e.preventDefault();
    if (!llmForm.provider || !llmForm.model.trim()) {
      notify("Provider and model are required.", "error");
      return;
    }
    if (llmForm.provider === "openai_compatible" && !llmForm.base_url.trim()) {
      notify("OpenAI-compatible vendors require a base URL.", "error");
      return;
    }
    setLoading(true);
    try {
      const saved = await api<LLMProviderConfig>("/admin/llm-config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: llmForm.provider,
          model: llmForm.model.trim(),
          base_url: llmForm.base_url.trim(),
          api_key: llmForm.api_key.trim() || null,
        }),
      });
      setLlmConfig(saved);
      setLlmForm({ provider: saved.provider, model: saved.model, base_url: saved.base_url, api_key: "" });
      notify("LLM configuration updated.");
      await refreshDashboard();
    } catch (err) {
      notify(`LLM configuration failed: ${err instanceof Error ? err.message : String(err)}`, "error");
    } finally {
      setLoading(false);
    }
  }

  async function generateDesign(requirementId: number, primaryReviewers?: string[]) {
    setLoading(true);
    try {
      const body: Record<string, unknown> = { requested_by: user?.email || "system" };
      if (primaryReviewers && primaryReviewers.length > 0) {
        body.primary_reviewer_emails = primaryReviewers;
      }
      await api(`/designs/generate/${requirementId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
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

  function openReviewerPicker(reqId: number, reqTitle: string) {
    const primaryUsers = allUsers.filter(u => ["primary_reviewer", "admin"].includes(u.role));
    const defaultReviewer = primaryUsers.length > 0 ? primaryUsers[0].email : "";
    setReviewerPick({ reqId, reqTitle, selectedReviewers: defaultReviewer ? [defaultReviewer] : [], andGenerate: false });
  }

  async function confirmGenerate() {
    if (!reviewerPick.reqId) return;
    const reviewers = reviewerPick.selectedReviewers.filter(Boolean);
    setReviewerPick({ reqId: null, reqTitle: "", selectedReviewers: [], andGenerate: false });
    await generateDesign(reviewerPick.reqId, reviewers.length > 0 ? reviewers : undefined);
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

  async function exportDesign(designId: number, fileFormat: "md" | "docx" | "pdf", version?: "draft" | "final") {
    try {
      const exportVersion = version || "draft";
      const res = await fetch(`${API_BASE}/designs/${designId}/export?version=${exportVersion}&file_format=${fileFormat}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) {
        const detail = await res.text();
        throw new Error(detail);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const disposition = res.headers.get("content-disposition") || "";
      const filenameMatch = disposition.match(/filename="?([^"]+)"?/i);
      a.download = filenameMatch?.[1] || `design-${designId}.${fileFormat}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      notify(`Export failed: ${err instanceof Error ? err.message : String(err)}`, "error");
    }
  }

  async function viewDesign(designId: number) {
    setLoading(true);
    try {
      const detail = await api<DesignDetail>(`/designs/${designId}`);
      setSelectedDesign(detail);
    } catch (err) {
      notify(`Could not load design: ${err instanceof Error ? err.message : String(err)}`, "error");
    } finally {
      setLoading(false);
    }
  }

  // ── Login page ──────────────────────────────────────────────────────────────
  if (!token || !user) {
    return (
      <div className="login-shell">
        <div className="login-card">
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
  const canViewLeadership = ["admin", "leadership", "svp", "executive"].includes(user.role);
  const pendingReviews = reviews.filter((r) => r.status === "PENDING").length;

  async function clearAllData() {
    if (!window.confirm("This will permanently delete ALL requirements, designs, reviews and training documents. Users are kept. Continue?")) return;
    setClearing(true);
    try {
      await api("/admin/reset-data", { method: "DELETE" });
      notify("All data cleared. Starting fresh.", "success");
      await refreshDashboard();
    } catch (err) {
      notify(`Clear failed: ${err instanceof Error ? err.message : String(err)}`, "error");
    } finally {
      setClearing(false);
    }
  }

  const tabs: { id: Tab; label: string; badge?: number }[] = [
    { id: "dashboard", label: "🏠 Dashboard" },
    ...(canViewLeadership ? [{ id: "leaderboard" as Tab, label: "Leadership" }] : []),
    { id: "requirements", label: "Requirements" },
    { id: "designs", label: "Designs" },
    ...(canEdit ? [{ id: "training" as Tab, label: "Training Library" }] : []),
    ...(canReview ? [{ id: "reviews" as Tab, label: "Reviews", badge: pendingReviews }] : []),
    ...(canViewLeadership ? [{ id: "usage" as Tab, label: "Usage" }] : []),
    ...(user.role === "admin" ? [{ id: "users" as Tab, label: "👥 Users" }] : []),
    ...(user.role === "admin" ? [{ id: "llm-config" as Tab, label: "LLM Config" }] : []),
    ...(user.role === "admin" ? [{ id: "reports" as Tab, label: "Reports" }] : []),
  ];

  return (
    <div className="shell">
      {/* Topbar */}
      <header className="topbar">
        <div className="topbar-brand">
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

      {/* ── Reviewer Picker Modal ───────────────────────────────────────── */}
      {reviewerPick.reqId !== null && (
        <div className="modal-backdrop">
          <div className="modal-card" style={{
            padding: 28, minWidth: 440, maxWidth: 520,
          }}>
            <p style={{ margin: "0 0 4px", fontWeight: 700, fontSize: 16, color: "var(--text)" }}>
              Select Primary Reviewer
            </p>
            <p style={{ margin: "0 0 20px", color: "var(--muted)", fontSize: 13 }}>
              for: <strong style={{ color: "var(--text)" }}>{reviewerPick.reqTitle}</strong>
            </p>
            {allUsers.filter(u => ["primary_reviewer", "admin"].includes(u.role)).length === 0 ? (
              <div className="alert alert-info" style={{ marginBottom: 16 }}>
                No primary_reviewer users found. <span style={{ cursor: "pointer", textDecoration: "underline" }} onClick={() => { setReviewerPick({ reqId: null, reqTitle: "", selectedReviewers: [], andGenerate: false }); setActiveTab("users"); }}>Create one →</span>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 20 }}>
                {allUsers
                  .filter(u => ["primary_reviewer", "admin"].includes(u.role))
                  .map(u => {
                    const checked = reviewerPick.selectedReviewers.includes(u.email);
                    return (
                      <label key={u.email} style={{
                        display: "flex", alignItems: "center", gap: 12, padding: "10px 14px",
                        borderRadius: 8, border: `1px solid ${checked ? "var(--accent)" : "var(--border)"}`,
                        background: checked ? "rgba(91,155,212,0.08)" : "var(--surface2)",
                        cursor: "pointer", fontSize: 14,
                      }}>
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => {
                            const list = reviewerPick.selectedReviewers.includes(u.email)
                              ? reviewerPick.selectedReviewers.filter(e => e !== u.email)
                              : [...reviewerPick.selectedReviewers, u.email];
                            setReviewerPick({ ...reviewerPick, selectedReviewers: list });
                          }}
                          style={{ accentColor: "var(--accent)", width: 16, height: 16 }}
                        />
                        <div>
                          <div style={{ fontWeight: 600, color: "var(--text)" }}>{u.full_name}</div>
                          <div style={{ color: "var(--muted)", fontSize: 12 }}>{u.email} · {u.role.replace(/_/g, " ")}</div>
                        </div>
                      </label>
                    );
                  })}
              </div>
            )}

            <div className="row" style={{ gap: 10, justifyContent: "flex-end" }}>
              <button
                className="btn-secondary"
                onClick={() => setReviewerPick({ reqId: null, reqTitle: "", selectedReviewers: [], andGenerate: false })}
              >
                Cancel
              </button>
              <button
                style={{ background: "var(--red)", color: "white", border: "none", borderRadius: 6, padding: "8px 20px", fontWeight: 600, fontSize: 14, cursor: "pointer" }}
                disabled={loading}
                onClick={confirmGenerate}
              >
                {loading ? "Generating…" : "⚡ Generate & Send for Review"}
              </button>
            </div>
          </div>
        </div>
      )}

      <main className="content">
        {message && (
          <div className={`alert alert-${message.type}`}>
            {message.text}
          </div>
        )}

        {/* ── Dashboard tab ────────────────────────── */}
        {activeTab === "dashboard" && (
          <div>
            {/* Hero welcome bar */}
            <div style={{ marginBottom: 28, display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
              <div>
                <h2 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: "var(--text)" }}>
                  Welcome back, {user.full_name.split(" ")[0]} 👋
                </h2>
                <p style={{ margin: "4px 0 0", color: "var(--muted)", fontSize: 14 }}>
                  Here's the live state of the design pipeline.
                </p>
              </div>
              <div className="row" style={{ gap: 10 }}>
                <button className="btn-secondary btn-sm" onClick={refreshDashboard} disabled={loading}>
                  ↻ Refresh
                </button>
                {user.role === "admin" && (
                  <button className="btn-danger btn-sm" onClick={clearAllData} disabled={clearing}>
                    {clearing ? "Clearing…" : "🗑 Clear All Data"}
                  </button>
                )}
              </div>
            </div>

            {/* Stat cards — 5 column grid */}
            <div className="grid-5" style={{ marginBottom: 28 }}>
              <div className="stat-card" style={{ "--card-accent": "var(--accent)" } as React.CSSProperties}>
                <span className="stat-icon">📋</span>
                <span className="stat-value">{requirements.length}</span>
                <span className="stat-label">Requirements</span>
                <span className="stat-sub">Total in system</span>
              </div>
              <div className="stat-card" style={{ "--card-accent": "#7c5cbf" } as React.CSSProperties}>
                <span className="stat-icon">⚡</span>
                <span className="stat-value">{designs.length}</span>
                <span className="stat-label">Designs Generated</span>
                <span className="stat-sub">All time</span>
              </div>
              <div className="stat-card" style={{ "--card-accent": "var(--warning)" } as React.CSSProperties}>
                <span className="stat-icon">🔍</span>
                <span className="stat-value">
                  {designs.filter(d => ["UNDER_PRIMARY_REVIEW","UNDER_FINAL_REVIEW"].includes(d.status)).length}
                </span>
                <span className="stat-label">In Review</span>
                <span className="stat-sub">Awaiting decision</span>
              </div>
              <div className="stat-card" style={{ "--card-accent": "var(--success)" } as React.CSSProperties}>
                <span className="stat-icon">✅</span>
                <span className="stat-value">
                  {designs.filter(d => d.status === "FINAL_APPROVED").length}
                </span>
                <span className="stat-label">Approved</span>
                <span className="stat-sub">Final sign-off</span>
              </div>
              <div className="stat-card" style={{ "--card-accent": "#f85149" } as React.CSSProperties}>
                <span className="stat-icon">❌</span>
                <span className="stat-value">
                  {designs.filter(d => ["PRIMARY_REJECTED","FINAL_REWORK_REQUIRED"].includes(d.status)).length}
                </span>
                <span className="stat-label">Rejected / Rework</span>
                <span className="stat-sub">Need attention</span>
              </div>
            </div>

            {/* Two-column layout: pipeline status + activity feed */}
            <div className="grid">
              {/* Pipeline breakdown */}
              <div className="panel">
                <p className="panel-title">Pipeline Breakdown</p>
                {designs.length === 0 ? (
                  <div className="empty" style={{ padding: "24px 0" }}>No designs yet. Generate one from Requirements.</div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                    {[
                      { label: "Pending Generation", key: "PENDING", color: "var(--muted)" },
                      { label: "Under Primary Review", key: "UNDER_PRIMARY_REVIEW", color: "var(--warning)" },
                      { label: "Under Final Review", key: "UNDER_FINAL_REVIEW", color: "var(--accent)" },
                      { label: "Final Approved", key: "FINAL_APPROVED", color: "var(--success)" },
                      { label: "Rework Required", key: "FINAL_REWORK_REQUIRED", color: "#d29922" },
                      { label: "Rejected", key: "PRIMARY_REJECTED", color: "#f85149" },
                    ].map(({ label, key, color }) => {
                      const count = designs.filter(d => d.status === key).length;
                      const pct = designs.length ? (count / designs.length) * 100 : 0;
                      return (
                        <div key={key}>
                          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                            <span style={{ fontSize: 13, color: "var(--text)" }}>{label}</span>
                            <span style={{ fontSize: 13, fontWeight: 700, color }}>{count}</span>
                          </div>
                          <div style={{ background: "var(--border)", borderRadius: 4, height: 6 }}>
                            <div style={{ width: `${pct}%`, height: 6, borderRadius: 4, background: color, transition: "width 0.4s" }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Pending reviews callout */}
                {pendingReviews > 0 && (
                  <div className="alert alert-info" style={{ marginTop: 20, marginBottom: 0 }}>
                    🔔 You have <strong>{pendingReviews}</strong> pending review{pendingReviews > 1 ? "s" : ""}.{" "}
                    <span
                      style={{ cursor: "pointer", textDecoration: "underline" }}
                      onClick={() => setActiveTab("reviews")}
                    >
                      Go to Reviews →
                    </span>
                  </div>
                )}
              </div>

              {/* Recent activity feed */}
              <div className="panel">
                <p className="panel-title">Recent Activity</p>
                {!reportSummary || reportSummary.recent_events.length === 0 ? (
                  <div className="empty" style={{ padding: "24px 0" }}>No events recorded yet.</div>
                ) : (
                  <div>
                    {reportSummary.recent_events.slice(0, 10).map((ev) => {
                      const dotColor =
                        ev.status === "SUCCESS" ? "var(--success)"
                        : ev.status === "FAILED" ? "#f85149"
                        : "var(--accent)";
                      return (
                        <div className="activity-item" key={ev.id}>
                          <div className="activity-dot" style={{ background: dotColor }} />
                          <div>
                            <p className="activity-text">
                              <strong>{ev.event_type.replace(/_/g, " ")}</strong>
                              {" — "}{ev.entity_type} #{ev.entity_id}
                            </p>
                            <p className="activity-time">
                              by {ev.actor_email} &nbsp;·&nbsp; {new Date(ev.created_at).toLocaleString()}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* Quick-action cards (non-admin see only what's relevant) */}
            <div className="grid-3" style={{ marginTop: 24 }}>
              <div
                className="stat-card"
                style={{ cursor: "pointer", "--card-accent": "var(--red)" } as React.CSSProperties}
                onClick={() => setActiveTab("requirements")}
              >
                <span className="stat-icon">➕</span>
                <span className="stat-label">New Requirement</span>
                <span className="stat-sub">Paste email or call notes</span>
              </div>
              <div
                className="stat-card"
                style={{ cursor: "pointer", "--card-accent": "var(--accent)" } as React.CSSProperties}
                onClick={() => setActiveTab("designs")}
              >
                <span className="stat-icon">📄</span>
                <span className="stat-label">View Designs</span>
                <span className="stat-sub">Export MD / DOCX / PDF</span>
              </div>
              {canReview && (
                <div
                  className="stat-card"
                  style={{ cursor: "pointer", "--card-accent": "var(--warning)" } as React.CSSProperties}
                  onClick={() => setActiveTab("reviews")}
                >
                  <span className="stat-icon">🔍</span>
                  <span className="stat-label">Review Queue</span>
                  <span className="stat-sub">{pendingReviews} pending</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Requirements tab ─────────────────────── */}
        {activeTab === "requirements" && (
          <div>
            {canEdit && (
              <div className="panel" style={{ marginBottom: 24 }}>
                <p className="panel-title">New Program Requirement</p>
                <p className="hint" style={{ marginBottom: 16 }}>
                  Paste requirement notes or upload a PDF/DOCX/TXT requirement. The system normalizes it before design generation.
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

                  {/* Discovery Questionnaire — structured companion to the free-text requirement below */}
                  <div style={{ marginBottom: 20, padding: 16, borderRadius: 8, border: "1px solid var(--border)", background: "var(--surface2)" }}>
                    <p style={{ margin: "0 0 4px", fontWeight: 700, fontSize: 14, color: "var(--text)" }}>
                      Discovery Questionnaire <span style={{ fontWeight: 400, color: "var(--muted)" }}>(optional)</span>
                    </p>
                    <p className="hint" style={{ marginTop: 0, marginBottom: 14 }}>
                      Answer as many of these as you know. They ground the generated design in unambiguous facts —
                      anything not covered here can still go in Requirement Details below.
                    </p>
                    <DiscoveryQuestionnaire
                      value={reqForm.discovery}
                      onChange={(next: DiscoveryAnswers) => setReqForm({ ...reqForm, discovery: next })}
                    />
                  </div>

                  <div className="field" style={{ marginBottom: 16 }}>
                    <label>Requirement File</label>
                    <input
                      type="file"
                      accept=".txt,.md,.pdf,.docx"
                      onChange={(e) => setReqForm({ ...reqForm, file: e.target.files?.[0] || null })}
                    />
                    <p className="hint" style={{ marginTop: 4 }}>
                      Optional. If a file is uploaded, it will be used instead of the pasted text.
                    </p>
                  </div>

                  {/* Requirement text area */}
                  <div className="field" style={{ marginBottom: 16 }}>
                    <label>Requirement Details {!reqForm.file && <span style={{ color: "var(--red)" }}>*</span>}</label>
                    <textarea
                      value={reqForm.rawText}
                      onChange={(e) => setReqForm({ ...reqForm, rawText: e.target.value })}
                      rows={10}
                      placeholder={`Paste the email or type the requirement here.\n\nExample:\n"We need a 40-hour program on React and Node.js for a batch of 25 experienced Java developers at Infosys. The program should cover frontend fundamentals, hooks, REST API integration, and deployment to AWS. Pre-requisites are basic JavaScript and Git knowledge."`}
                      required={!reqForm.file}
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
                              <button className="btn-sm" onClick={() => openReviewerPicker(r.id, r.title)} disabled={loading}>
                                ⚡ Generate Design
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
                    <th>Download</th>
                  </tr>
                </thead>
                <tbody>
                  {designs.map((d) => {
                    const score = d.similarity_score;
                    const finalApproved = d.status === "FINAL_APPROVED";
                    const needsRework = ["PRIMARY_REJECTED", "FINAL_REWORK_REQUIRED"].includes(d.status);
                    return (
                      <tr key={d.id}>
                        <td className="hint">{d.id}</td>
                        <td style={{ fontWeight: 600 }}>{d.title}</td>
                        <td>{statusBadge(d.status)}</td>
                        <td>
                          <div className="row" style={{ gap: 8, alignItems: "center" }}>
                            <div className="score-bar-wrap" style={{ width: 80 }}>
                              <div className={`score-bar${scoreBarClass(score)}`} style={{ width: percentWidth(score) }} />
                            </div>
                            <span className="hint">{formatPercent(score)}</span>
                          </div>
                        </td>
                        <td className="hint">{d.created_by}</td>
                        <td>
                          <div className="row" style={{ gap: 6 }}>
                            <button className="btn-sm btn-secondary" onClick={() => viewDesign(d.id)}>View</button>
                            {needsRework && canEdit && (
                              <button className="btn-sm btn-accent" onClick={() => openReviewerPicker(d.requirement_id, d.title)} disabled={loading}>
                                Regenerate
                              </button>
                            )}
                            <button className="btn-sm btn-outline" onClick={() => exportDesign(d.id, "md")}>Draft MD</button>
                            <button className="btn-sm btn-outline" onClick={() => exportDesign(d.id, "docx")}>Draft DOCX</button>
                            <button className="btn-sm btn-success" onClick={() => exportDesign(d.id, "docx", "final")} disabled={!finalApproved} title={finalApproved ? "Download approved final design" : "Final design unlocks after both final approvals"}>
                              Final Design
                            </button>
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
                      <th>Chunks</th>
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
                        <td>{t.chunk_count || 0}</td>
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

        {selectedDesign && (
          <div className="modal-backdrop" onClick={() => setSelectedDesign(null)}>
            <div className="modal-card design-detail" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <div>
                  <p className="panel-title" style={{ marginBottom: 8 }}>{selectedDesign.title}</p>
                  <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
                    {statusBadge(selectedDesign.status)}
                    <span className="hint">Design #{selectedDesign.id}</span>
                    <span className="hint">Updated {new Date(selectedDesign.updated_at).toLocaleString()}</span>
                  </div>
                </div>
                <button className="btn-secondary btn-sm" onClick={() => setSelectedDesign(null)}>Close</button>
              </div>

              <div className="grid-3" style={{ marginBottom: 20 }}>
                <div className="metric metric-accent">
                  <span className="metric-value">{selectedDesign.scorecard ? formatPercent(selectedDesign.scorecard.overall_score) : "N/A"}</span>
                  <span className="metric-label">Design Accuracy</span>
                </div>
                <div className="metric metric-accent">
                  <span className="metric-value">{formatPercent(selectedDesign.similarity_score)}</span>
                  <span className="metric-label">Reuse Similarity</span>
                </div>
                <div className="metric metric-accent">
                  <span className="metric-value">{selectedDesign.references.length}</span>
                  <span className="metric-label">References Used</span>
                </div>
              </div>

              {selectedDesign.scorecard && (
                <div className="panel" style={{ marginBottom: 16 }}>
                  <p className="panel-title">Quality Scorecard</p>
                  <div className="score-grid">
                    {[
                      ["Requirement Coverage", selectedDesign.scorecard.requirement_coverage_score],
                      ["Template Completeness", selectedDesign.scorecard.template_completeness_score],
                      ["Technical Consistency", selectedDesign.scorecard.technical_consistency_score],
                      ["Reuse Relevance", selectedDesign.scorecard.reuse_relevance_score],
                      ["Risk Quality", selectedDesign.scorecard.risk_quality_score],
                      ["Review Readiness", selectedDesign.scorecard.review_readiness_score],
                      ["LLM Evaluation", selectedDesign.scorecard.llm_evaluation_score],
                    ].map(([label, value]) => (
                      <div key={label as string} className="score-row">
                        <span>{label}</span>
                        <div className="score-bar-wrap">
                          <div className={`score-bar${scoreBarClass(value as number)}`} style={{ width: percentWidth(value as number) }} />
                        </div>
                        <strong>{formatPercent(value as number)}</strong>
                      </div>
                    ))}
                  </div>
                  {selectedDesign.scorecard.notes && <p className="hint" style={{ marginTop: 14 }}>{selectedDesign.scorecard.notes}</p>}
                  {(selectedDesign.scorecard.missing_requirements.length > 0 || selectedDesign.scorecard.contradictions.length > 0) && (
                    <div className="grid" style={{ marginTop: 16 }}>
                      <div>
                        <p className="label">Missing Requirements</p>
                        <ul className="compact-list">
                          {selectedDesign.scorecard.missing_requirements.map((item) => <li key={item}>{item}</li>)}
                        </ul>
                      </div>
                      <div>
                        <p className="label">Contradictions</p>
                        <ul className="compact-list">
                          {selectedDesign.scorecard.contradictions.map((item) => <li key={item}>{item}</li>)}
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              )}

              <div className="panel" style={{ marginBottom: 16 }}>
                <p className="panel-title">Retrieved References</p>
                {selectedDesign.references.length === 0 ? (
                  <div className="empty" style={{ padding: "18px 0" }}>No reusable references were found.</div>
                ) : (
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Source</th>
                        <th>Title</th>
                        <th>Match</th>
                        <th>Sections</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedDesign.references.map((ref, idx) => (
                        <tr key={`${ref.source_type}-${ref.source_title}-${idx}`}>
                          <td>{ref.source_type.replace(/_/g, " ")}</td>
                          <td>{ref.source_title}</td>
                          <td>{formatPercent(ref.similarity_score)}</td>
                          <td className="hint">{ref.reused_sections.join(", ") || "General context"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              <div className="panel" style={{ marginBottom: 0 }}>
                <div className="row" style={{ justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                  <p className="panel-title" style={{ margin: 0 }}>Design Preview</p>
                  <div className="row" style={{ gap: 8 }}>
                    <button className="btn-sm btn-outline" onClick={() => exportDesign(selectedDesign.id, "docx")}>
                      Draft DOCX
                    </button>
                    <button
                      className="btn-sm btn-success"
                      onClick={() => exportDesign(selectedDesign.id, "docx", "final")}
                      disabled={selectedDesign.status !== "FINAL_APPROVED"}
                      title={selectedDesign.status === "FINAL_APPROVED" ? "Download approved final design" : "Final design unlocks after both final approvals"}
                    >
                      Download Final Design
                    </button>
                  </div>
                </div>
                {selectedDesign.status !== "FINAL_APPROVED" && (
                  <div className="alert alert-info">
                    Final design download will be available after primary approval and both final reviewer approvals are complete.
                  </div>
                )}
                <pre className="design-preview">{selectedDesign.final_content || selectedDesign.draft_content}</pre>
              </div>
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

        {/* ── Users tab ────────────────────────────── */}
        {activeTab === "users" && user.role === "admin" && (
          <div>
            {/* Create user form */}
            <div className="panel" style={{ marginBottom: 24 }}>
              <p className="panel-title">Create New User</p>
              <p className="hint" style={{ marginBottom: 16 }}>
                Add designers, primary reviewers, or final reviewers. They will be available in the reviewer dropdown when generating designs.
              </p>
              <form onSubmit={createUser}>
                <div className="grid" style={{ marginBottom: 12 }}>
                  <div className="field">
                    <label>Full Name <span style={{ color: "var(--red)" }}>*</span></label>
                    <input
                      value={userForm.full_name}
                      onChange={e => setUserForm({ ...userForm, full_name: e.target.value })}
                      placeholder="e.g. Priya Sharma"
                      required
                    />
                  </div>
                  <div className="field">
                    <label>Email Address <span style={{ color: "var(--red)" }}>*</span></label>
                    <input
                      type="email"
                      value={userForm.email}
                      onChange={e => setUserForm({ ...userForm, email: e.target.value })}
                      placeholder="e.g. priya.sharma@niit.com"
                      required
                    />
                  </div>
                </div>
                <div className="grid" style={{ marginBottom: 16 }}>
                  <div className="field">
                    <label>Role <span style={{ color: "var(--red)" }}>*</span></label>
                    <select
                      value={userForm.role}
                      onChange={e => setUserForm({ ...userForm, role: e.target.value })}
                      style={{ height: 38, borderRadius: 6, border: "1px solid var(--border)", background: "var(--surface2)", color: "var(--text)", padding: "0 10px", fontSize: 14 }}
                    >
                      <option value="designer">Designer — creates and submits designs</option>
                      <option value="primary_reviewer">Primary Reviewer — first approval gate</option>
                      <option value="final_reviewer">Final Reviewer — final sign-off</option>
                      <option value="leadership">Leadership — leadership dashboard only</option>
                      <option value="admin">Admin — full access</option>
                    </select>
                  </div>
                  <div className="field">
                    <label>Password <span style={{ color: "var(--red)" }}>*</span></label>
                    <input
                      type="password"
                      value={userForm.password}
                      onChange={e => setUserForm({ ...userForm, password: e.target.value })}
                      placeholder="Minimum 8 characters"
                      required
                    />
                  </div>
                </div>
                <button type="submit" disabled={loading} style={{ minWidth: 160 }}>
                  {loading ? "Creating…" : "Create User"}
                </button>
              </form>
            </div>

            {/* User list */}
            <div className="panel">
              <p className="panel-title">All Users ({allUsers.length})</p>
              {allUsers.length === 0 ? (
                <div className="empty">No users found.</div>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Full Name</th>
                      <th>Email</th>
                      <th>Role</th>
                      <th>Status</th>
                      <th>Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {allUsers.map(u => (
                      <tr key={u.id}>
                        <td className="hint">{u.id}</td>
                        <td style={{ fontWeight: 600 }}>{u.full_name}</td>
                        <td className="hint">{u.email}</td>
                        <td>
                          <span style={{
                            display: "inline-block", padding: "2px 10px", borderRadius: 12, fontSize: 12, fontWeight: 600,
                            background: u.role === "admin" ? "rgba(233,113,50,0.15)" : u.role === "primary_reviewer" ? "rgba(91,155,212,0.15)" : u.role === "final_reviewer" ? "rgba(58,163,127,0.15)" : "rgba(125,133,144,0.15)",
                            color: u.role === "admin" ? "var(--red)" : u.role === "primary_reviewer" ? "var(--accent)" : u.role === "final_reviewer" ? "var(--success)" : "var(--muted)",
                          }}>
                            {u.role.replace(/_/g, " ")}
                          </span>
                        </td>
                        <td>{statusBadge(u.is_active ? "ACTIVE" : "REJECTED")}</td>
                        <td className="hint">{new Date(u.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* ── LLM Config tab ────────────────────────── */}
        {activeTab === "llm-config" && user.role === "admin" && (
          <div>
            <div className="panel" style={{ marginBottom: 24 }}>
              <p className="panel-title">LLM Provider Configuration</p>
              <p className="hint" style={{ marginBottom: 16 }}>
                Default is local Ollama. Switch here only when the business has approved API access for Claude, OpenAI, Groq, or another OpenAI-compatible vendor.
              </p>
              {llmConfig && (
                <div className="alert alert-info">
                  Active provider: <strong>{llmConfig.provider.replace(/_/g, " ")}</strong> using <strong>{llmConfig.model}</strong>
                  {llmConfig.has_api_key ? " with API key saved." : " with no API key saved."}
                </div>
              )}
              <form onSubmit={saveLlmConfig}>
                <div className="grid" style={{ marginBottom: 12 }}>
                  <div className="field">
                    <label>Provider</label>
                    <select
                      value={llmForm.provider}
                      onChange={e => {
                        const provider = e.target.value;
                        const defaults: Record<string, { model: string; base_url: string }> = {
                          ollama: { model: "qwen2.5:7b-instruct", base_url: "http://localhost:11434" },
                          groq: { model: "llama-3.3-70b-versatile", base_url: "" },
                          anthropic: { model: "claude-3-5-sonnet-latest", base_url: "" },
                          openai: { model: "gpt-4o", base_url: "" },
                          openai_compatible: { model: "", base_url: "" },
                        };
                        setLlmForm({ ...llmForm, provider, ...defaults[provider], api_key: "" });
                      }}
                    >
                      <option value="ollama">Ollama Local LLM</option>
                      <option value="groq">Groq</option>
                      <option value="anthropic">Claude / Anthropic</option>
                      <option value="openai">OpenAI</option>
                      <option value="openai_compatible">Other OpenAI-Compatible Vendor</option>
                    </select>
                  </div>
                  <div className="field">
                    <label>Model</label>
                    <input
                      value={llmForm.model}
                      onChange={e => setLlmForm({ ...llmForm, model: e.target.value })}
                      placeholder="e.g. claude-3-5-sonnet-latest"
                      required
                    />
                  </div>
                </div>
                <div className="grid" style={{ marginBottom: 16 }}>
                  <div className="field">
                    <label>Base URL</label>
                    <input
                      value={llmForm.base_url}
                      onChange={e => setLlmForm({ ...llmForm, base_url: e.target.value })}
                      placeholder={llmForm.provider === "openai_compatible" ? "https://vendor.example.com/v1" : "Only needed for Ollama or compatible vendors"}
                    />
                  </div>
                  <div className="field">
                    <label>API Key</label>
                    <input
                      type="password"
                      value={llmForm.api_key}
                      onChange={e => setLlmForm({ ...llmForm, api_key: e.target.value })}
                      placeholder={llmConfig?.has_api_key ? "Leave blank to keep existing key" : "Paste provider API key"}
                    />
                  </div>
                </div>
                <button type="submit" disabled={loading} style={{ minWidth: 180 }}>
                  {loading ? "Saving..." : "Save LLM Configuration"}
                </button>
              </form>
            </div>

            <div className="panel">
              <p className="panel-title">Provider Notes</p>
              <div className="compact-list">
                <div><strong>Ollama:</strong> private local default, no API key needed.</div>
                <div><strong>Claude:</strong> requires an Anthropic API key, not a Claude web subscription.</div>
                <div><strong>OpenAI/Groq:</strong> requires vendor API key and approved business use.</div>
                <div><strong>Other vendors:</strong> use OpenAI-compatible chat-completions base URL.</div>
              </div>
            </div>
          </div>
        )}

        {/* ── Leadership tab ───────────────────────── */}
        {activeTab === "leaderboard" && canViewLeadership && leadershipSummary && (
          <div className="leadership-page">
            <div className="executive-hero">
              <div>
                <p className="eyebrow">Leadership Command Center</p>
                <h2>Design Automation Performance</h2>
                <p>
                  Adoption, throughput, approval health, final design downloads, and LLM spend in one operating view.
                </p>
              </div>
              <div className="executive-hero-score">
                <span>{formatPercent(leadershipSummary.success_rate)}</span>
                <small>approval success rate</small>
              </div>
            </div>

            <div className="executive-kpi-grid">
              <div className="metric metric-accent executive-kpi">
                <span className="metric-value">{leadershipSummary.active_tool_users_count}</span>
                <span className="metric-label">Active Tool Users</span>
                <span className="metric-note">{leadershipSummary.active_users_count} active accounts</span>
              </div>
              <div className="metric metric-accent executive-kpi">
                <span className="metric-value">{leadershipSummary.designs_generated_count}</span>
                <span className="metric-label">Designs Generated</span>
                <span className="metric-note">{leadershipSummary.requirements_count} requirements received</span>
              </div>
              <div className="metric metric-accent executive-kpi">
                <span className="metric-value">{leadershipSummary.final_approved_count}</span>
                <span className="metric-label">Successfully Approved</span>
                <span className="metric-note">{leadershipSummary.pending_review_count} still pending review</span>
              </div>
              <div className="metric metric-accent executive-kpi">
                <span className="metric-value">{formatPercent(leadershipSummary.success_rate)}</span>
                <span className="metric-label">Success Rate</span>
                <span className="metric-note">approved / generated designs</span>
              </div>
              <div className="metric metric-accent executive-kpi">
                <span className="metric-value">{formatPercent(leadershipSummary.average_design_score)}</span>
                <span className="metric-label">Avg Design Score</span>
                <span className="metric-note">quality and readiness score</span>
              </div>
              <div className="metric metric-accent executive-kpi">
                <span className="metric-value">{leadershipSummary.pdf_exports_count}</span>
                <span className="metric-label">Final Designs Downloaded</span>
                <span className="metric-note">approved deliverables exported</span>
              </div>
              <div className="metric metric-accent executive-kpi">
                <span className="metric-value">{leadershipSummary.rejected_or_rework_count}</span>
                <span className="metric-label">Rejected / Rework</span>
                <span className="metric-note">items needing attention</span>
              </div>
              <div className="metric metric-accent executive-kpi">
                <span className="metric-value">{usageSummary ? usageSummary.total_calls : 0}</span>
                <span className="metric-label">LLM Calls</span>
                <span className="metric-note">generation calls tracked</span>
              </div>
              <div className="metric metric-accent executive-kpi">
                <span className="metric-value">{usageSummary ? usageSummary.total_tokens.toLocaleString() : "0"}</span>
                <span className="metric-label">Tokens Used</span>
                <span className="metric-note">input + output tokens</span>
              </div>
              <div className="metric metric-accent executive-kpi">
                <span className="metric-value">${usageSummary ? usageSummary.estimated_cost.toFixed(4) : "0.0000"}</span>
                <span className="metric-label">Est. LLM Spend</span>
                <span className="metric-note">provider-reported estimate</span>
              </div>
            </div>

            <div className="executive-chart-grid">
              <div className="panel executive-panel">
                <p className="panel-title">Generation Funnel</p>
                {[
                  ["Requirements", leadershipSummary.requirements_count, "var(--accent)"],
                  ["Generated Designs", leadershipSummary.designs_generated_count, "var(--red)"],
                  ["Final Approved", leadershipSummary.final_approved_count, "var(--success)"],
                  ["Final Downloads", leadershipSummary.pdf_exports_count, "var(--warning)"],
                ].map(([label, value, color]) => {
                  const maxValue = Math.max(leadershipSummary.requirements_count, leadershipSummary.designs_generated_count, 1);
                  const width = Math.max(8, Math.round((Number(value) / maxValue) * 100));
                  return (
                    <div key={label as string} style={{ marginBottom: 14 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
                        <span className="hint">{label}</span>
                        <strong>{value}</strong>
                      </div>
                      <div className="executive-bar-track">
                        <div className="executive-bar" style={{ width: `${width}%`, background: color as string }} />
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="panel executive-panel">
                <p className="panel-title">Approval Mix</p>
                {[
                  ["Approved", leadershipSummary.final_approved_count, "var(--success)"],
                  ["Pending Review", leadershipSummary.pending_review_count, "var(--warning)"],
                  ["Rejected / Rework", leadershipSummary.rejected_or_rework_count, "#f85149"],
                ].map(([label, value, color]) => {
                  const total = Math.max(
                    leadershipSummary.final_approved_count + leadershipSummary.pending_review_count + leadershipSummary.rejected_or_rework_count,
                    1,
                  );
                  const width = Math.max(8, Math.round((Number(value) / total) * 100));
                  return (
                    <div key={label as string} style={{ marginBottom: 14 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
                        <span className="hint">{label}</span>
                        <strong>{formatPercent(Number(value) / total)}</strong>
                      </div>
                      <div className="executive-bar-track">
                        <div className="executive-bar" style={{ width: `${width}%`, background: color as string }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="executive-chart-grid">
              <div className="panel executive-panel">
                <p className="panel-title">Token Spend Snapshot</p>
                {!usageSummary || usageSummary.total_calls === 0 ? (
                  <div className="empty" style={{ padding: "24px 0" }}>
                    No token usage recorded yet. Generate a new design to populate this view.
                  </div>
                ) : (
                  <div>
                    {usageSummary.by_user.slice(0, 5).map((row) => {
                      const maxTokens = Math.max(...usageSummary.by_user.map((item) => item.total_tokens), 1);
                      const width = Math.max(8, Math.round((row.total_tokens / maxTokens) * 100));
                      return (
                        <div key={row.user_email} style={{ marginBottom: 14 }}>
                          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
                            <span className="hint">{row.user_email}</span>
                            <strong>{row.total_tokens.toLocaleString()} tokens</strong>
                          </div>
                          <div className="executive-bar-track">
                            <div className="executive-bar" style={{ width: `${width}%`, background: "var(--accent)" }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              <div className="panel executive-panel">
                <p className="panel-title">LLM Cost Overview</p>
                <div className="grid-3">
                  <div className="metric metric-accent">
                    <span className="metric-value">{usageSummary ? usageSummary.prompt_tokens.toLocaleString() : "0"}</span>
                    <span className="metric-label">Input Tokens</span>
                  </div>
                  <div className="metric metric-accent">
                    <span className="metric-value">{usageSummary ? usageSummary.completion_tokens.toLocaleString() : "0"}</span>
                    <span className="metric-label">Output Tokens</span>
                  </div>
                  <div className="metric metric-accent">
                    <span className="metric-value">{usageSummary ? usageSummary.by_user.length : 0}</span>
                    <span className="metric-label">Users</span>
                  </div>
                </div>
                <p className="hint" style={{ marginTop: 16 }}>
                  Spend is estimated from captured provider token metadata. Claude/OpenAI enterprise providers can feed the same dashboard once connected.
                </p>
              </div>
            </div>

            <div className="panel">
              <p className="panel-title">Recent Leadership Activity</p>
              {leadershipSummary.recent_events.length === 0 ? (
                <div className="empty">No activity recorded yet.</div>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Event</th>
                      <th>Entity</th>
                      <th>Actor</th>
                      <th>Status</th>
                      <th>Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leadershipSummary.recent_events.map((event) => (
                      <tr key={event.id}>
                        <td style={{ fontWeight: 600 }}>{event.event_type.replace(/_/g, " ")}</td>
                        <td className="hint">{event.entity_type} #{event.entity_id}</td>
                        <td className="hint">{event.actor_email}</td>
                        <td>{statusBadge(event.status)}</td>
                        <td className="hint">{new Date(event.created_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* ── Usage tab ─────────────────────────────── */}
        {activeTab === "usage" && canViewLeadership && usageSummary && (
          <div>
            <div style={{ marginBottom: 24 }}>
              <h2 style={{ margin: 0, fontSize: 22 }}>LLM Usage</h2>
              <p className="hint" style={{ marginTop: 6 }}>
                Token usage and estimated cost across the active provider selected in Admin LLM Configuration.
              </p>
            </div>

            <div className="grid-3" style={{ marginBottom: 24 }}>
              <div className="metric metric-accent">
                <span className="metric-value">{usageSummary.total_calls}</span>
                <span className="metric-label">LLM Calls</span>
              </div>
              <div className="metric metric-accent">
                <span className="metric-value">{usageSummary.total_tokens.toLocaleString()}</span>
                <span className="metric-label">Total Tokens</span>
              </div>
              <div className="metric metric-accent">
                <span className="metric-value">${usageSummary.estimated_cost.toFixed(4)}</span>
                <span className="metric-label">Estimated Cost</span>
              </div>
              <div className="metric metric-accent">
                <span className="metric-value">{usageSummary.prompt_tokens.toLocaleString()}</span>
                <span className="metric-label">Input Tokens</span>
              </div>
              <div className="metric metric-accent">
                <span className="metric-value">{usageSummary.completion_tokens.toLocaleString()}</span>
                <span className="metric-label">Output Tokens</span>
              </div>
              <div className="metric metric-accent">
                <span className="metric-value">{usageSummary.by_user.length}</span>
                <span className="metric-label">Users Consuming LLM</span>
              </div>
            </div>

            <div className="grid" style={{ marginBottom: 24 }}>
              <div className="panel">
                <p className="panel-title">Usage by User</p>
                {usageSummary.by_user.length === 0 ? (
                  <div className="empty">No LLM usage recorded yet.</div>
                ) : (
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>User</th>
                        <th>Calls</th>
                        <th>Tokens</th>
                        <th>Est. Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {usageSummary.by_user.map((row) => (
                        <tr key={row.user_email}>
                          <td style={{ fontWeight: 600 }}>{row.user_email}</td>
                          <td>{row.calls_count}</td>
                          <td>{row.total_tokens.toLocaleString()}</td>
                          <td>${row.estimated_cost.toFixed(4)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              <div className="panel">
                <p className="panel-title">Recent LLM Calls</p>
                {usageSummary.recent_events.length === 0 ? (
                  <div className="empty">No LLM calls recorded yet.</div>
                ) : (
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Provider</th>
                        <th>User</th>
                        <th>Tokens</th>
                        <th>Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {usageSummary.recent_events.map((event) => (
                        <tr key={event.id}>
                          <td>{event.provider} / {event.model}</td>
                          <td className="hint">{event.user_email}</td>
                          <td>{event.total_tokens.toLocaleString()}</td>
                          <td>${event.estimated_cost.toFixed(4)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
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
                <span className="metric-value">{formatPercent(reportSummary.average_design_score)}</span>
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
