"use client";

import { useEffect, useState } from "react";
import type { AtsReport, ResumeVersion } from "@/lib/types";
import { api } from "@/lib/api-client";
import { Badge } from "@/components/atoms/Badge";
import { Button } from "@/components/atoms/Button";

interface AtsOptimizerProps {
  version: ResumeVersion;
  disabled?: boolean;
  onEdit: () => void;
  onRefine: (fingerprint: string) => Promise<void>;
}

export function AtsOptimizer({ version, disabled, onEdit, onRefine }: AtsOptimizerProps) {
  const [report, setReport] = useState<AtsReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [refining, setRefining] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setReport(null);
    api.getAtsReport(version.id)
      .then((result) => { if (!cancelled) setReport(result); })
      .catch((e: unknown) => { if (!cancelled) setError(e instanceof Error ? e.message : "Could not load ATS check"); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [version.id, version.updated_at]);

  const check = async () => {
    setChecking(true);
    setError(null);
    try {
      setReport(await api.checkAts(version.id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "ATS check failed");
    } finally {
      setChecking(false);
    }
  };

  const refine = async () => {
    if (!report || report.is_stale) return;
    setRefining(true);
    setError(null);
    try {
      await onRefine(report.fingerprint);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Refinement failed");
    } finally {
      setRefining(false);
    }
  };

  const busy = loading || checking || refining || disabled;

  return (
    <section className="min-w-0 space-y-4 rounded-lg border p-4 dark:border-gray-700 sm:p-6" aria-labelledby="ats-heading">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 id="ats-heading" className="text-lg font-semibold">ATS Optimizer</h3>
          <p className="mt-1 text-xs opacity-60">Seven local checks for resume v{version.version_no}.</p>
        </div>
        <Button variant="secondary" size="sm" disabled={busy} onClick={check}>
          {checking ? "Checking..." : report ? "Recheck ATS" : "Run ATS check"}
        </Button>
      </div>

      {loading && <p className="text-sm opacity-60" role="status">Loading ATS check...</p>}
      {error && <p role="alert" className="break-words rounded bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">{error}</p>}
      {!loading && !report && <p className="text-sm opacity-70">Check keyword coverage, action verbs, length, content formatting, quantified achievements, missing skills, and readability against this job.</p>}

      {report && (
        <>
          {report.is_stale && <p role="status" className="rounded bg-yellow-50 p-3 text-sm text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300">The resume or job has changed. Recheck ATS before refining; this score reflects older content.</p>}
          <div className="flex flex-wrap items-center gap-4 rounded-lg bg-gray-50 p-4 dark:bg-gray-800/60">
            <div className="text-3xl font-bold tabular-nums">{report.overall_score}<span className="text-base font-normal opacity-50"> / 100</span></div>
            <div className="space-y-1 text-xs opacity-70">
              <p>{report.word_count} words · {report.matched_keywords.length} matched job terms</p>
              {report.baseline_score !== null && <p>Baseline {report.baseline_score} → {report.overall_score} ({(report.score_delta ?? 0) > 0 ? "+" : ""}{report.score_delta ?? 0})</p>}
              <p>Content estimate, not an employer ATS score.</p>
            </div>
          </div>

          <div className="grid min-w-0 gap-3 sm:grid-cols-2">
            {report.checks.map((item) => (
              <div key={item.category} className="min-w-0 rounded-lg border p-3 dark:border-gray-700">
                <div className="flex items-start justify-between gap-2 text-sm font-medium">
                  <span>{item.label}</span>
                  <span className="shrink-0 tabular-nums">{item.score ?? "N/A"}{item.score !== null && <span className="font-normal opacity-40">/100</span>}</span>
                </div>
                {item.score !== null && <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700"><div className={`h-full rounded-full ${item.score >= 80 ? "bg-green-500" : item.score >= 60 ? "bg-yellow-500" : "bg-red-500"}`} style={{ width: `${item.score}%` }} /></div>}
                <p className="mt-2 break-words text-xs leading-relaxed opacity-60">{item.summary}</p>
              </div>
            ))}
          </div>

          {report.missing_skills.length > 0 && <div><h4 className="mb-2 text-sm font-semibold">Skills not evidenced in this resume</h4><div className="flex flex-wrap gap-1">{report.missing_skills.map((skill) => <span key={skill} className="max-w-full break-words rounded bg-red-50 px-2 py-1 text-xs text-red-700 dark:bg-red-900/20 dark:text-red-300">{skill}</span>)}</div></div>}

          <div>
            <h4 className="mb-2 text-sm font-semibold">Suggestions</h4>
            {report.suggestions.length === 0 ? <p className="text-sm opacity-60">No actionable suggestions from these checks. Review the resume for accuracy before applying.</p> : (
              <ul className="space-y-3">
                {report.suggestions.map((suggestion) => <li key={suggestion.category} className="min-w-0 space-y-1 rounded-lg bg-gray-50 p-3 dark:bg-gray-800/50"><Badge variant={suggestion.priority === "high" ? "red" : suggestion.priority === "medium" ? "yellow" : "gray"}>{suggestion.priority}</Badge><p className="break-words text-sm leading-relaxed">{suggestion.message}</p></li>)}
              </ul>
            )}
          </div>

          <div className="space-y-3 border-t pt-4 dark:border-gray-700">
            <div className="flex flex-wrap gap-2">
              <Button variant="primary" size="sm" disabled={busy || report.is_stale || report.suggestions.length === 0} onClick={refine}>{refining ? "Refining..." : "Refine into new version"}</Button>
              <Button variant="secondary" size="sm" disabled={busy} onClick={onEdit}>Edit manually</Button>
            </div>
            <p className="text-xs leading-relaxed opacity-60">Refinement uses your configured LLM, preserves this version, and scores the new version. New numbers and job skills are checked against source evidence. Review the resulting facts; a higher score is not guaranteed.</p>
            <details className="text-xs opacity-60"><summary className="cursor-pointer">How this score works</summary><ul className="mt-2 list-disc space-y-1 pl-4">{report.limitations.map((note) => <li key={note}>{note}</li>)}</ul><p className="mt-2">Scoring v{report.scoring_version} · <time dateTime={report.evaluated_at}>{new Date(report.evaluated_at).toLocaleString()}</time></p></details>
          </div>
        </>
      )}
    </section>
  );
}
