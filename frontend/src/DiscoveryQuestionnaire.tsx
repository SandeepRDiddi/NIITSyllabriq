// Mandatory structured companion to the free-text requirement intake.
// Renders the 11 Discovery Questionnaire questions as discrete controls.
// Pure presentational component — App.tsx owns the state and submission.
// A requirement does not qualify for design generation until every
// question here is answered — see missingDiscoveryQuestions() below.

export type DiscoveryAnswers = {
  domain_focus: string[];
  target_audience_roles: string[];
  experience_level: string;
  learner_count: string;
  trigger: string;
  delivery_model: string;
  timeline: string;
  constraints: string;
  strategic_objective: string[];
  prior_vendor_experience: string;
  expected_business_outcomes: string[];
};

export const EMPTY_DISCOVERY_ANSWERS: DiscoveryAnswers = {
  domain_focus: [],
  target_audience_roles: [],
  experience_level: "",
  learner_count: "",
  trigger: "",
  delivery_model: "",
  timeline: "",
  constraints: "",
  strategic_objective: [],
  prior_vendor_experience: "",
  expected_business_outcomes: [],
};

// Question key -> human label, used to report exactly which questions are
// unanswered when a requirement fails the design-qualification check.
// Mirrors DISCOVERY_QUESTION_LABELS in app/schemas/requirement.py.
const DISCOVERY_QUESTION_LABELS: Record<keyof DiscoveryAnswers, string> = {
  domain_focus: "Q1 domain focus",
  target_audience_roles: "Q2 target audience",
  experience_level: "Q3 experience level",
  learner_count: "Q4 learner count",
  trigger: "Q5 trigger",
  delivery_model: "Q6 delivery model",
  timeline: "Q7 timeline",
  constraints: "Q8 constraints",
  strategic_objective: "Q9 strategic objective",
  prior_vendor_experience: "Q10 prior vendor experience",
  expected_business_outcomes: "Q11 expected business outcomes",
};

export function missingDiscoveryQuestions(value: DiscoveryAnswers): string[] {
  const missing: string[] = [];
  (Object.keys(DISCOVERY_QUESTION_LABELS) as (keyof DiscoveryAnswers)[]).forEach((field) => {
    const answer = value[field];
    if (field === "learner_count") {
      const parsed = parseInt(String(answer || ""), 10);
      if (!answer || !Number.isFinite(parsed) || parsed <= 0) missing.push(DISCOVERY_QUESTION_LABELS[field]);
    } else if (Array.isArray(answer)) {
      if (answer.length === 0) missing.push(DISCOVERY_QUESTION_LABELS[field]);
    } else if (!String(answer || "").trim()) {
      missing.push(DISCOVERY_QUESTION_LABELS[field]);
    }
  });
  return missing;
}

const DOMAIN_FOCUS_OPTIONS = ["AI", "Data", "Cloud", "Cybersecurity", "Software Engineering", "DevOps", "Other"];
const AUDIENCE_ROLE_OPTIONS = ["Software Engineers", "QA Engineers", "Data Scientists", "Architects", "Managers", "Fresh Graduates", "Product Teams", "Other"];
const EXPERIENCE_LEVEL_OPTIONS = ["Freshers", "1–3 years", "3–5 years", "5+ years", "Tech Leads", "Managers", "Senior Leaders"];
const TRIGGER_OPTIONS = ["New Project", "Digital Transformation Initiative", "Skill Gap", "Compliance Requirement", "Hiring Plan", "Customer Demand", "Technology Adoption", "Other"];
const DELIVERY_MODEL_OPTIONS = ["Instructor-Led Training (ILT)", "Virtual Instructor-Led Training (VILT)", "Self-Paced Learning", "Blended Learning"];
const STRATEGIC_OBJECTIVE_OPTIONS = ["AI Adoption", "Cloud Migration", "Digital Transformation", "Platform Modernization", "GenAI Strategy", "Engineering Excellence", "Productivity Improvement", "Other"];
const BUSINESS_OUTCOME_OPTIONS = ["Faster Project Readiness", "Improved Productivity", "Certification Targets", "Reduced Defects", "Cloud Adoption", "Talent Retention", "Other"];

function toggle(list: string[], value: string): string[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value];
}

function ChipGroup({ options, selected, onChange }: { options: string[]; selected: string[]; onChange: (next: string[]) => void }) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
      {options.map((option) => {
        const checked = selected.includes(option);
        return (
          <label
            key={option}
            style={{
              display: "flex", alignItems: "center", gap: 6, padding: "6px 12px",
              borderRadius: 16, border: `1px solid ${checked ? "var(--accent)" : "var(--border)"}`,
              background: checked ? "rgba(91,155,212,0.08)" : "var(--surface2)",
              cursor: "pointer", fontSize: 13,
            }}
          >
            <input
              type="checkbox"
              checked={checked}
              onChange={() => onChange(toggle(selected, option))}
              style={{ accentColor: "var(--accent)", width: 14, height: 14 }}
            />
            {option}
          </label>
        );
      })}
    </div>
  );
}

export default function DiscoveryQuestionnaire({
  value,
  onChange,
}: {
  value: DiscoveryAnswers;
  onChange: (next: DiscoveryAnswers) => void;
}) {
  function set<K extends keyof DiscoveryAnswers>(key: K, fieldValue: DiscoveryAnswers[K]) {
    onChange({ ...value, [key]: fieldValue });
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div className="field">
        <label>1. Why are we discussing this requirement? (domain focus) <span style={{ color: "var(--red)" }}>*</span></label>
        <p className="hint" style={{ marginTop: 0, marginBottom: 6 }}>
          Capability gap, certification, project demand, or workforce transformation — which domain(s) is the focus?
        </p>
        <ChipGroup options={DOMAIN_FOCUS_OPTIONS} selected={value.domain_focus} onChange={(next) => set("domain_focus", next)} />
      </div>

      <div className="field">
        <label>2. Who is the target audience for this programme? <span style={{ color: "var(--red)" }}>*</span></label>
        <ChipGroup options={AUDIENCE_ROLE_OPTIONS} selected={value.target_audience_roles} onChange={(next) => set("target_audience_roles", next)} />
      </div>

      <div className="grid" style={{ gap: 16 }}>
        <div className="field">
          <label>3. What is the experience level of the learners? <span style={{ color: "var(--red)" }}>*</span></label>
          <select
            value={value.experience_level}
            onChange={(e) => set("experience_level", e.target.value)}
            required
            style={{ height: 38, borderRadius: 6, border: "1px solid var(--border)", padding: "0 10px", fontSize: 14 }}
          >
            <option value="">Select…</option>
            {EXPERIENCE_LEVEL_OPTIONS.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </div>

        <div className="field">
          <label>4. How many learners are expected to participate? <span style={{ color: "var(--red)" }}>*</span></label>
          <input
            type="number"
            min="1"
            value={value.learner_count}
            onChange={(e) => set("learner_count", e.target.value)}
            placeholder="e.g. 120"
            required
          />
        </div>
      </div>

      <div className="grid" style={{ gap: 16 }}>
        <div className="field">
          <label>5. What triggered this requirement? <span style={{ color: "var(--red)" }}>*</span></label>
          <select
            value={value.trigger}
            onChange={(e) => set("trigger", e.target.value)}
            required
            style={{ height: 38, borderRadius: 6, border: "1px solid var(--border)", padding: "0 10px", fontSize: 14 }}
          >
            <option value="">Select…</option>
            {TRIGGER_OPTIONS.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </div>

        <div className="field">
          <label>6. What is the preferred delivery model? <span style={{ color: "var(--red)" }}>*</span></label>
          <select
            value={value.delivery_model}
            onChange={(e) => set("delivery_model", e.target.value)}
            required
            style={{ height: 38, borderRadius: 6, border: "1px solid var(--border)", padding: "0 10px", fontSize: 14 }}
          >
            <option value="">Select…</option>
            {DELIVERY_MODEL_OPTIONS.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="field">
        <label>7. What is the expected timeline for the programme? <span style={{ color: "var(--red)" }}>*</span></label>
        <input
          value={value.timeline}
          onChange={(e) => set("timeline", e.target.value)}
          placeholder="Preferred start date, completion deadline, business milestones"
          required
        />
      </div>

      <div className="field">
        <label>8. Are there any constraints we should be aware of? <span style={{ color: "var(--red)" }}>*</span></label>
        <input
          value={value.constraints}
          onChange={(e) => set("constraints", e.target.value)}
          placeholder="Learner availability, business-critical periods, timezone, budget constraints (type 'None' if not applicable)"
          required
        />
      </div>

      <div className="field">
        <label>9. Is this initiative linked to a broader business or strategic objective? <span style={{ color: "var(--red)" }}>*</span></label>
        <ChipGroup options={STRATEGIC_OBJECTIVE_OPTIONS} selected={value.strategic_objective} onChange={(next) => set("strategic_objective", next)} />
      </div>

      <div className="field">
        <label>10. Have you previously engaged another vendor or training partner for a similar programme? <span style={{ color: "var(--red)" }}>*</span></label>
        <input
          value={value.prior_vendor_experience}
          onChange={(e) => set("prior_vendor_experience", e.target.value)}
          placeholder="What worked well? What challenges did you face? What would define success? (type 'None' if not applicable)"
          required
        />
      </div>

      <div className="field">
        <label>11. What business outcomes are you expecting from this programme? <span style={{ color: "var(--red)" }}>*</span></label>
        <ChipGroup options={BUSINESS_OUTCOME_OPTIONS} selected={value.expected_business_outcomes} onChange={(next) => set("expected_business_outcomes", next)} />
      </div>
    </div>
  );
}
