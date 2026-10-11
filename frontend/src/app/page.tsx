"use client";

import { useMemo, useState } from "react";
import { API_URL } from "@/lib/api";

type ContractData = {
  document_type: string | null;
  supplier: string | null;
  customer: string | null;
  finance_provider: string | null;
  currency: string | null;
  agreement_date: string | null;
  effective_date: string | null;
  installation_date: string | null;
  term_months: number | null;
  expiry_date: string | null;
  extension_expiry_date: string | null;
  equipment_rental_gbp: number | null;
  rental_frequency: string | null;
  monthly_base_fee_gbp: number | null;
  mono_cpc_gbp: number | null;
  colour_cpc_gbp: number | null;
  mono_overage_cpc_gbp: number | null;
  colour_overage_cpc_gbp: number | null;
  minimum_mono_monthly: number | null;
  minimum_colour_monthly: number | null;
  estimated_annual_contract_charge_gbp: number | null;
  annual_increase_description: string | null;
  annual_increase_fixed_percent: number | null;
  annual_increase_floor_percent: number | null;
  annual_increase_cap_percent: number | null;
  annual_increase_index: string | null;
  annual_increase_margin_percent: number | null;
  non_renewal_notice_days: number | null;
  extension_notice_days: number | null;
  termination_notice_days: number | null;
  termination_notice_working_days: number | null;
  auto_renewal_months: number | null;
  notice_window_start_days: number | null;
  notice_window_end_days: number | null;
  early_termination_description: string | null;
  equipment_collection_fee_gbp: number | null;
  payment_terms_days: number | null;
};

type EvidenceItem = {
  field: string;
  page: number;
  quote: string;
  verified: boolean;
};

type AnalysisResponse = {
  status: "complete" | "ocr_required";
  filename: string;
  page_count: number;
  message?: string;
  analysis?: ContractData;
  evidence?: EvidenceItem[];
  evidence_count?: number;
  verified_evidence_count?: number;
};

type FinancialResponse = {
  currency: string | null;
  annual_equipment_rental: number | null;
  annual_base_fee: number | null;
  annual_mono_cost: number | null;
  annual_colour_cost: number | null;
  annual_usage_cost: number | null;
  calculated_annual_cost: number | null;
  stated_annual_contract_value: number | null;
  is_partial: boolean;
  notes: string[];
};

function formatMoney(value: number | null | undefined, currency?: string | null) {
  if (value === null || value === undefined) return "Not found";

  try {
    return new Intl.NumberFormat("en-GB", {
      style: "currency",
      currency: currency || "GBP",
      maximumFractionDigits: 2,
    }).format(value);
  } catch {
    return `${currency || "GBP"} ${value.toLocaleString()}`;
  }
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">
        {label}
      </p>
      <div className="mt-2 break-words text-base font-semibold leading-6 text-slate-950">
        {value ?? "Not found"}
      </div>
    </div>
  );
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [monthlyMono, setMonthlyMono] = useState("");
  const [monthlyColour, setMonthlyColour] = useState("");
  const [financials, setFinancials] = useState<FinancialResponse | null>(null);
  const [calculating, setCalculating] = useState(false);

  const analysis = result?.analysis;
  const verifiedSummary = useMemo(() => {
    if (!result || result.status !== "complete") return null;
    return `${result.verified_evidence_count ?? 0}/${result.evidence_count ?? 0}`;
  }, [result]);

  async function analyseContract() {
    if (!file) return;

    setLoading(true);
    setError("");
    setResult(null);
    setFinancials(null);

    try {
      const body = new FormData();
      body.append("file", file);

      const response = await fetch(`${API_URL}/api/contracts/analyse`, {
        method: "POST",
        body,
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Contract analysis failed.");
      }

      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to analyse contract.");
    } finally {
      setLoading(false);
    }
  }

  async function calculateCosts() {
    if (!analysis) return;

    setCalculating(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/contracts/calculate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contract: analysis,
          usage: {
            monthly_mono_pages: Number(monthlyMono) || 0,
            monthly_colour_pages: Number(monthlyColour) || 0,
          },
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Cost calculation failed.");
      }

      setFinancials(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to calculate costs.");
    } finally {
      setCalculating(false);
    }
  }

  function reset() {
    setFile(null);
    setResult(null);
    setFinancials(null);
    setMonthlyMono("");
    setMonthlyColour("");
    setError("");
  }

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <button onClick={reset} className="text-left">
            <div className="text-2xl font-black tracking-tight text-slate-950">
              Print<span className="text-blue-600">Sift</span>
            </div>
            <p className="text-xs text-slate-500">Contract analysis portfolio project</p>
          </button>

          <a
            href="https://github.com/lukeacko/PrintSift-Portfolio"
            className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            View source
          </a>
        </div>
      </header>

      {!result && (
        <section className="mx-auto max-w-6xl px-6 py-20">
          <div className="mx-auto max-w-3xl text-center">
            <span className="inline-flex rounded-full border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-semibold text-blue-700">
              Python · FastAPI · Next.js · Structured AI
            </span>

            <h1 className="mt-7 text-5xl font-black tracking-[-0.04em] text-slate-950 sm:text-6xl">
              Understand what a copier contract actually says.
            </h1>

            <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-slate-600">
              PrintSift extracts commercial terms, verifies them against source evidence and calculates estimated annual costs from real usage.
            </p>
          </div>

          <div className="mx-auto mt-12 max-w-2xl rounded-[28px] border border-slate-200 bg-white p-6 shadow-xl shadow-slate-200/50">
            <label className="flex cursor-pointer flex-col items-center rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 px-6 py-10 text-center hover:border-blue-400 hover:bg-blue-50/50">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600 text-xl font-bold text-white">
                ↑
              </div>
              <p className="mt-4 font-semibold text-slate-950">
                {file ? file.name : "Choose a PDF contract"}
              </p>
              <p className="mt-1 text-sm text-slate-500">
                {file
                  ? `${(file.size / 1024 / 1024).toFixed(2)} MB selected`
                  : "PDF only · Maximum 20 MB"}
              </p>
              <input
                type="file"
                accept="application/pdf"
                className="hidden"
                onChange={(event) => {
                  setFile(event.target.files?.[0] ?? null);
                  setError("");
                }}
              />
            </label>

            <button
              onClick={analyseContract}
              disabled={!file || loading}
              className="mt-4 w-full rounded-xl bg-blue-600 px-5 py-4 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {loading ? "Analysing contract..." : "Analyse contract"}
            </button>

            {error && (
              <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="mt-5 grid gap-2 text-center text-xs font-medium text-slate-500 sm:grid-cols-3">
              <span>Evidence-backed results</span>
              <span>No PDF saved by this app</span>
              <span>AI calls use store=false</span>
            </div>
          </div>

          <div className="mx-auto mt-16 grid max-w-4xl gap-4 md:grid-cols-3">
            {[
              ["Extract", "Costs, dates, notice periods, renewal and termination terms."],
              ["Verify", "Every AI-supported value includes a source quote and page number."],
              ["Calculate", "Combine contract pricing with monthly mono and colour usage."],
            ].map(([title, text]) => (
              <div key={title} className="rounded-2xl border border-slate-200 bg-white p-6">
                <h2 className="font-bold text-slate-950">{title}</h2>
                <p className="mt-2 text-sm leading-6 text-slate-600">{text}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {result?.status === "ocr_required" && (
        <section className="mx-auto max-w-3xl px-6 py-20">
          <div className="rounded-[28px] border border-amber-200 bg-white p-8 shadow-sm">
            <p className="text-sm font-bold uppercase tracking-wider text-amber-700">
              OCR required
            </p>
            <h1 className="mt-3 text-3xl font-bold text-slate-950">This PDF appears image-only.</h1>
            <p className="mt-4 leading-7 text-slate-600">{result.message}</p>
            <button onClick={reset} className="mt-7 rounded-xl bg-slate-950 px-5 py-3 font-semibold text-white">
              Try another PDF
            </button>
          </div>
        </section>
      )}

      {result?.status === "complete" && analysis && (
        <section className="mx-auto max-w-6xl px-6 py-12">
          <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
            <div>
              <p className="text-sm font-bold uppercase tracking-wider text-blue-600">Analysis complete</p>
              <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-950">{result.filename}</h1>
              <p className="mt-2 text-sm text-slate-500">
                {result.page_count} pages · Evidence verified: {verifiedSummary}
              </p>
            </div>
            <button onClick={reset} className="rounded-xl border border-slate-200 bg-white px-5 py-3 font-semibold text-slate-700">
              New review
            </button>
          </div>

          <div className="mt-10 grid gap-4 md:grid-cols-3">
            <Field label="Supplier" value={analysis.supplier || "Not found"} />
            <Field label="Customer" value={analysis.customer || "Not found"} />
            <Field label="Document type" value={analysis.document_type || "Not found"} />
            <Field label="Term" value={analysis.term_months ? `${analysis.term_months} months` : "Not found"} />
            <Field label="Expiry" value={analysis.expiry_date || "Not found"} />
            <Field label="Auto renewal" value={analysis.auto_renewal_months ? `${analysis.auto_renewal_months} months` : "Not found"} />
            <Field label="Equipment rental" value={formatMoney(analysis.equipment_rental_gbp, analysis.currency)} />
            <Field label="Rental frequency" value={analysis.rental_frequency || "Not found"} />
            <Field label="Monthly base fee" value={formatMoney(analysis.monthly_base_fee_gbp, analysis.currency)} />
            <Field label="Mono CPC" value={formatMoney(analysis.mono_cpc_gbp, analysis.currency)} />
            <Field label="Colour CPC" value={formatMoney(analysis.colour_cpc_gbp, analysis.currency)} />
            <Field label="Payment terms" value={analysis.payment_terms_days ? `${analysis.payment_terms_days} days` : "Not found"} />
          </div>

          <div className="mt-10 rounded-[28px] border border-slate-200 bg-white p-7 shadow-sm">
            <div className="flex flex-col gap-2">
              <p className="text-sm font-bold uppercase tracking-wider text-blue-600">Cost calculator</p>
              <h2 className="text-2xl font-bold text-slate-950">Estimate annual contract cost</h2>
              <p className="text-sm leading-6 text-slate-500">
                Enter monthly usage. PrintSift combines it with the pricing extracted from the contract.
              </p>
            </div>

            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <label className="text-sm font-semibold text-slate-700">
                Monthly mono pages
                <input
                  inputMode="numeric"
                  value={monthlyMono}
                  onChange={(e) => setMonthlyMono(e.target.value)}
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-blue-500"
                  placeholder="e.g. 10000"
                />
              </label>
              <label className="text-sm font-semibold text-slate-700">
                Monthly colour pages
                <input
                  inputMode="numeric"
                  value={monthlyColour}
                  onChange={(e) => setMonthlyColour(e.target.value)}
                  className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-blue-500"
                  placeholder="e.g. 2500"
                />
              </label>
            </div>

            <button
              onClick={calculateCosts}
              disabled={calculating}
              className="mt-5 rounded-xl bg-blue-600 px-5 py-3 font-semibold text-white disabled:bg-slate-300"
            >
              {calculating ? "Calculating..." : "Calculate annual cost"}
            </button>

            {financials && (
              <div className="mt-7 grid gap-4 md:grid-cols-3">
                <Field label="Calculated annual cost" value={formatMoney(financials.calculated_annual_cost, financials.currency)} />
                <Field label="Annual equipment rental" value={formatMoney(financials.annual_equipment_rental, financials.currency)} />
                <Field label="Annual usage cost" value={formatMoney(financials.annual_usage_cost, financials.currency)} />
              </div>
            )}

            {financials?.notes?.length ? (
              <ul className="mt-5 space-y-2 rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
                {financials.notes.map((note) => (
                  <li key={note}>• {note}</li>
                ))}
              </ul>
            ) : null}
          </div>

          <div className="mt-10 rounded-[28px] border border-slate-200 bg-white p-7 shadow-sm">
            <p className="text-sm font-bold uppercase tracking-wider text-blue-600">Evidence trail</p>
            <h2 className="mt-2 text-2xl font-bold text-slate-950">Why PrintSift returned these values</h2>

            <div className="mt-6 space-y-3">
              {(result.evidence ?? []).map((item, index) => (
                <div key={`${item.field}-${index}`} className="rounded-2xl border border-slate-200 p-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-slate-900">{item.field}</span>
                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">Page {item.page}</span>
                    <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${item.verified ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
                      {item.verified ? "Verified" : "Check manually"}
                    </span>
                  </div>
                  <blockquote className="mt-3 text-sm italic leading-6 text-slate-600">“{item.quote}”</blockquote>
                </div>
              ))}
            </div>
          </div>

          {error && (
            <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
          )}
        </section>
      )}

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-8 text-sm leading-6 text-slate-500">
          Portfolio build. No real customer contracts, referral records, API keys or production databases are included in this repository.
        </div>
      </footer>
    </main>
  );
}
