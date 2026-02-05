"use client";

import { useState } from "react";

type GenerateResponse = {
  answer: string;
  confidence: number;
  model_id: string;
  evidence: { consistency_score: number; min_source_score: number; flags: string[] };
  bias: { bias_score: number; risk_level: string; flagged_terms: string[]; metrics?: Record<string, number> };
  governance: { status: string; reasons: string[]; policy_hits: Array<Record<string, unknown>>; decision_id: string };
  explainability: { explanation: Record<string, unknown> };
  sources: Array<{ id: string; title: string; snippet: string; score: number }>;
};

export default function Home() {
  const [tenantId, setTenantId] = useState("gov-dept-a");
  const [userId, setUserId] = useState("analyst-1");
  const [prompt, setPrompt] = useState(
    "Draft a policy memo on responsible AI usage in public services."
  );
  const [topK, setTopK] = useState(4);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [decisionList, setDecisionList] = useState<Array<Record<string, unknown>>>([]);
  const [decisionDetail, setDecisionDetail] = useState<Record<string, unknown> | null>(null);
  const [decisionId, setDecisionId] = useState("");
  const [reviewStatus, setReviewStatus] = useState("approved");
  const [reviewer, setReviewer] = useState("reviewer-1");
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewResult, setReviewResult] = useState<Record<string, unknown> | null>(null);

  const submit = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const resp = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tenant_id: tenantId, user_id: userId, prompt, top_k: topK }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data?.detail || "Request failed");
      }
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const loadDecisions = async () => {
    const qs = new URLSearchParams({ tenant_id: tenantId, status: "pending" });
    const resp = await fetch(`/api/decisions?${qs.toString()}`);
    const data = await resp.json();
    setDecisionList(Array.isArray(data) ? data : []);
  };

  const loadDecisionDetail = async () => {
    if (!decisionId) return;
    const resp = await fetch(`/api/decision/${decisionId}`);
    const data = await resp.json();
    setDecisionDetail(data);
  };

  const submitReview = async () => {
    if (!decisionId) return;
    const resp = await fetch(`/api/decision/${decisionId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: reviewStatus, reviewer, notes: reviewNotes }),
    });
    const data = await resp.json();
    setReviewResult(data);
  };

  return (
    <main>
      <header>
        <div>
          <span className="badge">GovAI Control Room</span>
          <h1>Governed Generation, on demand.</h1>
          <p>
            Jalankan prompt dengan pipeline Responsible AI lengkap: RAG grounding,
            evidence checks, bias metrics, governance policy, dan explainability.
          </p>
        </div>
        <div className="card">
          <h2>Quick Actions</h2>
          <div className="tag">RAG</div>
          <div className="tag">Bias</div>
          <div className="tag">Governance</div>
          <div className="tag">Explainability</div>
          <p>Gunakan panel ini untuk men-trigger pipeline dan review hasilnya.</p>
          <button onClick={submit} disabled={loading}>
            {loading ? "Memproses..." : "Run Pipeline"}
          </button>
        </div>
      </header>

      <section className="grid">
        <div className="card fade-in">
          <h2>Input</h2>
          <label>Tenant ID</label>
          <input value={tenantId} onChange={(e) => setTenantId(e.target.value)} />
          <label>User ID</label>
          <input value={userId} onChange={(e) => setUserId(e.target.value)} />
          <label>Prompt</label>
          <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} />
          <label>Top K</label>
          <input
            type="number"
            min={1}
            max={8}
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
          />
          <button className="secondary" onClick={submit} disabled={loading}>
            {loading ? "Mengirim..." : "Generate"}
          </button>
          {error && <p style={{ color: "#b00020" }}>{error}</p>}
        </div>

        <div className="card fade-in">
          <h2>Output Ringkas</h2>
          {result ? (
            <>
              <p><strong>Model</strong>: {result.model_id}</p>
              <p><strong>Confidence</strong>: {result.confidence}</p>
              <p><strong>Governance</strong>: {result.governance.status}</p>
              <p><strong>Evidence Consistency</strong>: {result.evidence?.consistency_score}</p>
              <p><strong>Bias Score</strong>: {result.bias.bias_score}</p>
              <h3>Answer</h3>
              <p>{result.answer}</p>
            </>
          ) : (
            <p>Belum ada hasil. Jalankan pipeline di sebelah kiri.</p>
          )}
        </div>

        <div className="card fade-in">
          <h2>Sources</h2>
          {result ? (
            result.sources.map((src) => (
              <div key={src.id} style={{ marginBottom: 12 }}>
                <strong>{src.title}</strong>
                <p>{src.snippet}</p>
                <div className="tag">score {src.score}</div>
              </div>
            ))
          ) : (
            <p>Sources akan tampil setelah generate.</p>
          )}
        </div>

        <div className="card fade-in">
          <h2>Governance & Evidence</h2>
          {result ? (
            <>
              <p><strong>Status</strong>: {result.governance.status}</p>
              <p><strong>Reasons</strong>: {result.governance.reasons?.join(", ") || "-"}</p>
              <p><strong>Evidence Flags</strong>: {result.evidence?.flags?.join(", ") || "-"}</p>
              <p><strong>Bias Risk</strong>: {result.bias.risk_level}</p>
              <pre>{JSON.stringify(result.explainability.explanation, null, 2)}</pre>
            </>
          ) : (
            <p>Panel ini akan menampilkan explainability lengkap.</p>
          )}
        </div>
      </section>

      <section className="grid" style={{ marginTop: 24 }}>
        <div className="card fade-in">
          <h2>Review Queue</h2>
          <p>Ambil keputusan yang statusnya pending.</p>
          <button className="secondary" onClick={loadDecisions}>Load Pending</button>
          <pre>{JSON.stringify(decisionList, null, 2)}</pre>
        </div>

        <div className="card fade-in">
          <h2>Decision Detail</h2>
          <label>Decision ID</label>
          <input value={decisionId} onChange={(e) => setDecisionId(e.target.value)} />
          <button className="secondary" onClick={loadDecisionDetail}>Load Detail</button>
          <pre>{JSON.stringify(decisionDetail, null, 2)}</pre>
        </div>

        <div className="card fade-in">
          <h2>Approve / Reject</h2>
          <label>Status</label>
          <select value={reviewStatus} onChange={(e) => setReviewStatus(e.target.value)}>
            <option value="approved">Approve</option>
            <option value="rejected">Reject</option>
            <option value="pending">Keep Pending</option>
          </select>
          <label>Reviewer</label>
          <input value={reviewer} onChange={(e) => setReviewer(e.target.value)} />
          <label>Notes</label>
          <textarea value={reviewNotes} onChange={(e) => setReviewNotes(e.target.value)} />
          <button onClick={submitReview}>Submit Review</button>
          <pre>{JSON.stringify(reviewResult, null, 2)}</pre>
        </div>
      </section>

      <footer>
        Backend berjalan di Docker/Kubernetes. Frontend ini siap deploy ke Vercel.
      </footer>
    </main>
  );
}
