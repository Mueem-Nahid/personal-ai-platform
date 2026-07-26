"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import type { JobAnalysis, JobPost, Profile } from "@/lib/types";
import { api } from "@/lib/api-client";
import { Badge } from "@/components/atoms/Badge";
import { Button } from "@/components/atoms/Button";
import { ErrorBanner } from "@/components/organisms/ErrorBanner";
import { PageHeader } from "@/components/organisms/PageHeader";

const POLL_TIMEOUT = 120000;
const POLL_INTERVAL = 2000;

export default function JobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.jobId as string;
  const isMounted = useRef(false);

  const [job, setJob] = useState<JobPost | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<string>("");
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisMessage, setAnalysisMessage] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<JobAnalysis | null>(null);

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  const loadJob = useCallback(async () => {
    try {
      setLoading(true);
      const j = await api.getJob(jobId);
      if (isMounted.current) setJob(j);
    } catch (e) {
      if (isMounted.current) setError(e instanceof Error ? e.message : "Failed to load job");
    } finally {
      if (isMounted.current) setLoading(false);
    }
  }, [jobId]);

  const loadProfiles = useCallback(async () => {
    try {
      const p = await api.listProfiles();
      if (isMounted.current) {
        setProfiles(p);
        if (p.length > 0 && !selectedProfileId) {
          setSelectedProfileId(p[0].id!);
        }
      }
    } catch {
      // profiles are optional
    }
  }, [selectedProfileId]);

  const loadExistingAnalysis = useCallback(async () => {
    try {
      const result = await api.listAnalyses({ job_id: jobId });
      if (isMounted.current && result.analyses.length > 0) {
        const latest = result.analyses[0];
        setAnalysis(latest.status !== "analyzing" ? latest : null);
        if (latest.profile_id) setSelectedProfileId(latest.profile_id);
      }
    } catch {
      // no existing analysis is fine
    }
  }, [jobId]);

  useEffect(() => {
    loadJob();
    loadProfiles();
    loadExistingAnalysis();
  }, [loadJob, loadProfiles, loadExistingAnalysis]);

  const pollAnalysis = async (analysisId: string): Promise<void> => {
    const start = Date.now();
    let attempts = 0;
    while (isMounted.current) {
      if (Date.now() - start > POLL_TIMEOUT) {
        throw new Error("Analysis timed out");
      }
      await new Promise((r) => setTimeout(r, POLL_INTERVAL));
      try {
        const a = await api.getAnalysis(analysisId);
        if (a.status !== "analyzing") {
          if (isMounted.current) setAnalysis(a);
          return;
        }
        attempts += 1;
        if (isMounted.current) {
          setAnalysisMessage(`Analyzing${".".repeat((attempts % 3) + 1)}`);
        }
      } catch (e) {
        if (isMounted.current) console.warn("Poll attempt failed:", e);
      }
    }
  };

  const handleAnalyze = async () => {
    if (!selectedProfileId) return;
    setAnalyzing(true);
    setAnalysisMessage("Starting analysis...");
    setError(null);
    setAnalysis(null);
    try {
      const { analysis_id } = await api.startAnalysis(jobId, selectedProfileId);
      await pollAnalysis(analysis_id);
      setAnalysisMessage(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      if (isMounted.current) {
        setAnalyzing(false);
        setAnalysisMessage(null);
      }
    }
  };

  const fields = job?.parsed_fields;

  if (loading) {
    return <p className="text-sm opacity-50">Loading job...</p>;
  }

  if (!job) {
    return <ErrorBanner error="Job not found" onDismiss={() => router.push("/jobs")} />;
  }

  return (
    <div>
      <PageHeader
        title={fields?.title || job.title || "Job Detail"}
        backHref="/jobs"
      />

      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-1">
          <JobInfoSection job={job} />

          <div className="rounded-lg border p-4 dark:border-gray-700">
            <h3 className="mb-3 text-sm font-semibold opacity-70">Analyze with Profile</h3>
            {profiles.length === 0 ? (
              <p className="text-sm opacity-50">
                No profiles found. Create one in the{" "}
                <a href="/profile" className="underline hover:opacity-75">Profile Editor</a>{" "}
                first.
              </p>
            ) : (
              <>
                <select
                  value={selectedProfileId}
                  onChange={(e) => setSelectedProfileId(e.target.value)}
                  className="mb-3 w-full rounded border px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                  disabled={analyzing}
                >
                  {profiles.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.full_name}
                    </option>
                  ))}
                </select>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleAnalyze}
                  disabled={analyzing || !selectedProfileId}
                  className="w-full"
                >
                  {analyzing ? "Analyzing..." : "Analyze Fit"}
                </Button>
                {analysisMessage && (
                  <p className="mt-2 text-sm text-blue-600 dark:text-blue-400">
                    {analysisMessage}
                  </p>
                )}
              </>
            )}
          </div>
        </div>

        <div className="space-y-4 lg:col-span-2">
          {analysis && analysis.status === "analyzed" && analysis.report ? (
            <AnalysisReportSection analysis={analysis} />
          ) : analysis && analysis.status === "failed" ? (
            <div className="rounded-lg border border-red-200 p-4 dark:border-red-800">
              <p className="text-sm font-medium text-red-600 dark:text-red-400">
                Analysis Failed
              </p>
              <p className="mt-1 text-sm opacity-70">{analysis.error || "Unknown error"}</p>
              <Button variant="ghost" size="sm" onClick={handleAnalyze} className="mt-3">
                Retry
              </Button>
            </div>
          ) : (
            <div className="rounded-lg border p-8 text-center dark:border-gray-700">
              <p className="text-sm opacity-50">
                Select a profile and click &quot;Analyze Fit&quot; to see how you match this job.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function JobInfoSection({ job }: { job: JobPost }) {
  const fields = job.parsed_fields;
  return (
    <div className="rounded-lg border p-4 dark:border-gray-700 space-y-3">
      <div>
        <p className="font-medium">{fields?.company || "Unknown company"}</p>
        <p className="text-sm opacity-70">{fields?.location || "No location"}</p>
      </div>

      {fields?.salary && (
        <p className="text-sm font-medium text-green-600 dark:text-green-400">{fields.salary}</p>
      )}

      {fields?.employment_type && (
        <div>
          <span className="text-xs font-medium opacity-50">Type</span>
          <p className="text-sm">{fields.employment_type}</p>
        </div>
      )}

      {fields?.experience && (
        <div>
          <span className="text-xs font-medium opacity-50">Experience</span>
          <p className="text-sm">{fields.experience}</p>
        </div>
      )}

      {(fields?.skills?.length ?? 0) > 0 && (
        <div>
          <span className="text-xs font-medium opacity-50">Skills</span>
          <div className="mt-1 flex flex-wrap gap-1">
            {fields!.skills!.map((s) => <Badge key={s} variant="gray">{s}</Badge>)}
          </div>
        </div>
      )}

      {(fields?.tech_stack?.length ?? 0) > 0 && (
        <div>
          <span className="text-xs font-medium opacity-50">Tech Stack</span>
          <div className="mt-1 flex flex-wrap gap-1">
            {fields!.tech_stack!.map((t) => <Badge key={t} variant="gray">{t}</Badge>)}
          </div>
        </div>
      )}

      {job.raw_text && (
        <details>
          <summary className="cursor-pointer text-xs font-medium opacity-50 hover:opacity-75">
            Raw Text
          </summary>
          <p className="mt-1 whitespace-pre-wrap text-xs opacity-60">
            {job.raw_text.slice(0, 2000)}
            {job.raw_text.length > 2000 ? "..." : ""}
          </p>
        </details>
      )}
    </div>
  );
}

function AnalysisReportSection({ analysis }: { analysis: JobAnalysis }) {
  const r = analysis.report;
  if (!r) return null;

  return (
    <div className="rounded-lg border p-6 dark:border-gray-700 space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold">Fit Analysis</h3>
          <p className="text-xs opacity-50">via {analysis.provider} / {analysis.model}</p>
        </div>
        {r.fit_score != null && (
          <ScoreBadge score={r.fit_score} label="Fit" />
        )}
      </div>

      {r.recommendation && (
        <div className={`rounded px-3 py-2 text-sm font-medium ${
          r.recommendation === "apply"
            ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
            : r.recommendation === "apply-with-prep"
              ? "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400"
              : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
        }`}>
          Recommendation: {r.recommendation === "apply-with-prep" ? "Apply with Prep" : r.recommendation}
          {r.justification ? ` — ${r.justification}` : ""}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {r.ats_score != null && (
          <ScoreBadge score={r.ats_score} label="ATS Score" />
        )}
        {r.interview_difficulty && (
          <div className="rounded-lg border p-3 text-center dark:border-gray-600">
            <span className="text-xs font-medium opacity-50">Interview Difficulty</span>
            <p className="mt-1 text-lg font-semibold capitalize">{r.interview_difficulty}</p>
          </div>
        )}
      </div>

      {r.company_summary && (
        <div>
          <h4 className="text-sm font-semibold opacity-70">Company Summary</h4>
          <p className="mt-1 text-sm">{r.company_summary}</p>
        </div>
      )}

      {r.experience_fit && (
        <div>
          <h4 className="text-sm font-semibold opacity-70">Experience Fit</h4>
          <p className="mt-1 text-sm">{r.experience_fit}</p>
        </div>
      )}

      {(r.matched_skills?.length ?? 0) > 0 && (
        <ChipSection title="Matched Skills" items={r.matched_skills!} variant="green" />
      )}

      {(r.missing_skills?.length ?? 0) > 0 && (
        <ChipSection title="Missing Skills" items={r.missing_skills!} variant="red" />
      )}

      {(r.adjacent_strengths?.length ?? 0) > 0 && (
        <BulletSection title="Adjacent Strengths" items={r.adjacent_strengths!} />
      )}

      {(r.strengths?.length ?? 0) > 0 && (
        <BulletSection title="Strengths" items={r.strengths!} />
      )}

      {(r.weaknesses?.length ?? 0) > 0 && (
        <BulletSection title="Weaknesses" items={r.weaknesses!} />
      )}

      {(r.culture_signals?.length ?? 0) > 0 && (
        <ChipSection title="Culture Signals" items={r.culture_signals!} variant="gray" />
      )}

      {(r.likely_interview_topics?.length ?? 0) > 0 && (
        <ChipSection title="Likely Interview Topics" items={r.likely_interview_topics!} variant="blue" />
      )}
    </div>
  );
}

function ScoreBadge({ score, label }: { score: number; label: string }) {
  const color =
    score >= 75
      ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
      : score >= 50
        ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400"
        : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400";
  return (
    <div className={`rounded-lg border p-3 text-center dark:border-gray-600`}>
      <span className="text-xs font-medium opacity-50">{label}</span>
      <p className={`mt-1 text-lg font-bold ${color} rounded px-2 py-0.5 inline-block`}>
        {score}/100
      </p>
    </div>
  );
}

function ChipSection({
  title,
  items,
  variant,
}: {
  title: string;
  items: string[];
  variant: "gray" | "green" | "red" | "blue";
}) {
  return (
    <div>
      <h4 className="mb-2 text-sm font-semibold opacity-70">{title}</h4>
      <div className="flex flex-wrap gap-1">
        {items.map((item) => (
          <Badge key={item} variant={variant}>{item}</Badge>
        ))}
      </div>
    </div>
  );
}

function BulletSection({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <h4 className="mb-2 text-sm font-semibold opacity-70">{title}</h4>
      <ul className="list-disc space-y-1 pl-5 text-sm">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
