"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import type { JobAnalysis, JobAnalysisTrace, JobPost, MasterResume, Profile, ResumeVersion, ResumeVersionTrace } from "@/lib/types";
import { api } from "@/lib/api-client";
import { Badge } from "@/components/atoms/Badge";
import { Button } from "@/components/atoms/Button";
import { ErrorBanner } from "@/components/organisms/ErrorBanner";
import { PageHeader } from "@/components/organisms/PageHeader";
import { ResumeVersionCard } from "@/components/molecules/ResumeVersionCard";

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
  const [trace, setTrace] = useState<JobAnalysisTrace | null>(null);
  const [traceOpen, setTraceOpen] = useState(false);

  const [masterResumes, setMasterResumes] = useState<MasterResume[]>([]);
  const [selectedMasterId, setSelectedMasterId] = useState<string>("");
  const [resumeVersions, setResumeVersions] = useState<ResumeVersion[]>([]);
  const [buildingResume, setBuildingResume] = useState(false);
  const [resumeMessage, setResumeMessage] = useState<string | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<ResumeVersion | null>(null);
  const [versionTrace, setVersionTrace] = useState<ResumeVersionTrace | null>(null);
  const [versionTraceOpen, setVersionTraceOpen] = useState(false);

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

  const loadResumeData = useCallback(async (profileId: string) => {
    if (!profileId) return;
    try {
      const masters = await api.listMasterResumes(profileId);
      if (isMounted.current) {
        setMasterResumes(masters.resumes.filter((r) => r.status === "active"));
        if (masters.resumes.length > 0) {
          setSelectedMasterId((prev) => {
            if (prev) return prev;
            const def = masters.resumes.find((r) => r.is_default);
            return def ? def.id : masters.resumes[0].id;
          });
        }
      }
      const versions = await api.listResumeVersions(profileId, jobId);
      if (isMounted.current) {
        setResumeVersions(versions.versions);
      }
    } catch {
      // resume data optional
    }
  }, [jobId]);

  useEffect(() => {
    loadJob();
    loadProfiles();
    loadExistingAnalysis();
  }, [loadJob, loadProfiles, loadExistingAnalysis]);

  useEffect(() => {
    if (selectedProfileId) {
      loadResumeData(selectedProfileId);
    }
  }, [selectedProfileId, loadResumeData]);

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

  const handleToggleTrace = async (analysisId: string) => {
    if (trace) {
      setTraceOpen(!traceOpen);
      return;
    }
    try {
      const t = await api.getAnalysisTrace(analysisId);
      if (isMounted.current) {
        setTrace(t);
        setTraceOpen(true);
      }
    } catch {
      // trace fetch failure is non-fatal
    }
  };

  const handleAnalyze = async () => {
    if (!selectedProfileId) return;
    setAnalyzing(true);
    setAnalysisMessage("Starting analysis...");
    setError(null);
    setAnalysis(null);
    setTrace(null);
    setTraceOpen(false);
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

  const pollResumeVersion = async (versionId: string): Promise<void> => {
    const start = Date.now();
    let attempts = 0;
    while (isMounted.current) {
      if (Date.now() - start > POLL_TIMEOUT) {
        throw new Error("Resume build timed out");
      }
      await new Promise((r) => setTimeout(r, POLL_INTERVAL));
      try {
        const v = await api.getResumeVersion(versionId);
        if (v.status !== "building") {
          if (isMounted.current) {
            setResumeVersions((prev) => {
              const idx = prev.findIndex((rv) => rv.id === v.id);
              if (idx >= 0) {
                const next = [...prev];
                next[idx] = v;
                return next;
              }
              return [v, ...prev];
            });
            setSelectedVersion(v);
          }
          return;
        }
        attempts += 1;
        if (isMounted.current) {
          setResumeMessage(`Building${".".repeat((attempts % 3) + 1)}`);
        }
      } catch (e) {
        if (isMounted.current) console.warn("Poll attempt failed:", e);
      }
    }
  };

  const handleBuildResume = async () => {
    if (!selectedProfileId || !selectedMasterId) return;
    setBuildingResume(true);
    setResumeMessage("Starting build...");
    setError(null);
    try {
      const { resume_version_id, version_no } = await api.buildResume(
        selectedProfileId,
        jobId,
        selectedMasterId
      );
      const pendingVersion: ResumeVersion = {
        id: resume_version_id,
        profile_id: selectedProfileId,
        job_id: jobId,
        master_resume_id: selectedMasterId,
        version_no,
        status: "building",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setResumeVersions((prev) => [pendingVersion, ...prev]);
      await pollResumeVersion(resume_version_id);
      setResumeMessage(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Resume build failed");
    } finally {
      if (isMounted.current) {
        setBuildingResume(false);
        setResumeMessage(null);
      }
    }
  };

  const handleViewVersion = async (version: ResumeVersion) => {
    setSelectedVersion(version);
    setVersionTrace(null);
    setVersionTraceOpen(false);
  };

  const handleDeleteVersion = async (versionId: string) => {
    try {
      await api.deleteResumeVersion(versionId);
      setResumeVersions((prev) => prev.filter((v) => v.id !== versionId));
      if (selectedVersion?.id === versionId) setSelectedVersion(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  };

  const handleVersionTrace = async (versionId: string) => {
    if (versionTrace) {
      setVersionTraceOpen(!versionTraceOpen);
      return;
    }
    try {
      const t = await api.getResumeVersionTrace(versionId);
      if (isMounted.current) {
        setVersionTrace(t);
        setVersionTraceOpen(true);
      }
    } catch {
      // trace fetch failure is non-fatal
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
          {analysis && analysis.status === "analyzed" && (
            <details
              className="rounded-lg border dark:border-gray-700"
              open={traceOpen}
              onToggle={async (e) => {
                if ((e.target as HTMLDetailsElement).open && !trace) {
                  await handleToggleTrace(analysis.id);
                } else {
                  setTraceOpen((e.target as HTMLDetailsElement).open);
                }
              }}
            >
              <summary className="cursor-pointer p-4 text-sm font-medium opacity-70 hover:opacity-100">
                Audit Trail — inspect what the LLM saw
              </summary>
              <div className="border-t p-4 space-y-4 dark:border-gray-600">
                {!trace ? (
                  <p className="text-sm opacity-50">Loading...</p>
                ) : (
                  <>
                    {trace.evidence_text && (
                      <details>
                        <summary className="cursor-pointer text-xs font-medium opacity-50 hover:opacity-75">
                          Retrieved CV Evidence
                        </summary>
                        <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap rounded bg-gray-50 p-3 text-xs dark:bg-gray-800">
                          {trace.evidence_text}
                        </pre>
                      </details>
                    )}
                    {trace.prompt_text && (
                      <details>
                        <summary className="cursor-pointer text-xs font-medium opacity-50 hover:opacity-75">
                          Full Prompt Sent to LLM
                        </summary>
                        <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap rounded bg-gray-50 p-3 text-xs dark:bg-gray-800">
                          {trace.prompt_text}
                        </pre>
                      </details>
                    )}
                    {trace.raw_response && (
                      <details>
                        <summary className="cursor-pointer text-xs font-medium opacity-50 hover:opacity-75">
                          Raw LLM Response
                        </summary>
                        <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap rounded bg-gray-50 p-3 text-xs dark:bg-gray-800">
                          {trace.raw_response}
                        </pre>
                      </details>
                    )}
                  </>
                )}
              </div>
            </details>
          )}

          <div className="rounded-lg border p-4 dark:border-gray-700">
            <h3 className="mb-3 text-sm font-semibold opacity-70">Resume Builder</h3>
            {profiles.length === 0 ? (
              <p className="text-sm opacity-50">Create a profile first.</p>
            ) : masterResumes.length === 0 ? (
              <p className="text-sm opacity-50">
                No master resume. Upload one in{" "}
                <a href="/knowledge" className="underline hover:opacity-75">Knowledge Base</a>{" "}
                then designate it as master.
              </p>
            ) : (
              <>
                <select
                  value={selectedMasterId}
                  onChange={(e) => setSelectedMasterId(e.target.value)}
                  className="mb-3 w-full rounded border px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                  disabled={buildingResume}
                >
                  {masterResumes.map((m) => (
                    <option key={m.id} value={m.id}>
                      Master Resume{m.is_default ? " (default)" : ""}
                    </option>
                  ))}
                </select>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleBuildResume}
                  disabled={buildingResume || !selectedMasterId}
                  className="w-full"
                >
                  {buildingResume ? "Building..." : resumeVersions.length > 0
                    ? `Build Tailored v${(resumeVersions[0]?.version_no ?? 0) + 1}`
                    : "Build Tailored Resume"}
                </Button>
                {resumeMessage && (
                  <p className="mt-2 text-sm text-blue-600 dark:text-blue-400">
                    {resumeMessage}
                  </p>
                )}
              </>
            )}
          </div>

          {resumeVersions.length > 0 && (
            <div className="rounded-lg border p-4 dark:border-gray-700">
              <h3 className="mb-3 text-sm font-semibold opacity-70">Versions</h3>
              <div className="space-y-2">
                {resumeVersions.map((v) => (
                  <ResumeVersionCard
                    key={v.id}
                    version={v}
                    onView={() => handleViewVersion(v)}
                    onDelete={() => handleDeleteVersion(v.id)}
                  />
                ))}
              </div>
              {selectedVersion && selectedVersion.status === "built" && (
                <details
                  className="mt-4 rounded-lg border dark:border-gray-600"
                  open={versionTraceOpen}
                  onToggle={async (e) => {
                    if ((e.target as HTMLDetailsElement).open && !versionTrace) {
                      await handleVersionTrace(selectedVersion.id);
                    } else {
                      setVersionTraceOpen((e.target as HTMLDetailsElement).open);
                    }
                  }}
                >
                  <summary className="cursor-pointer p-3 text-xs font-medium opacity-50 hover:opacity-75">
                    Audit Trail
                  </summary>
                  <div className="border-t p-3 space-y-3 dark:border-gray-600">
                    {!versionTrace ? (
                      <p className="text-xs opacity-50">Loading...</p>
                    ) : (
                      <>
                        {versionTrace.evidence_text && (
                          <details>
                            <summary className="cursor-pointer text-xs font-medium opacity-50 hover:opacity-75">
                              Retrieved CV Evidence
                            </summary>
                            <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap rounded bg-gray-50 p-2 text-xs dark:bg-gray-800">
                              {versionTrace.evidence_text}
                            </pre>
                          </details>
                        )}
                        {versionTrace.prompt_text && (
                          <details>
                            <summary className="cursor-pointer text-xs font-medium opacity-50 hover:opacity-75">
                              Full Prompt
                            </summary>
                            <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap rounded bg-gray-50 p-2 text-xs dark:bg-gray-800">
                              {versionTrace.prompt_text}
                            </pre>
                          </details>
                        )}
                        {versionTrace.raw_response && (
                          <details>
                            <summary className="cursor-pointer text-xs font-medium opacity-50 hover:opacity-75">
                              Raw LLM Response
                            </summary>
                            <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap rounded bg-gray-50 p-2 text-xs dark:bg-gray-800">
                              {versionTrace.raw_response}
                            </pre>
                          </details>
                        )}
                      </>
                    )}
                  </div>
                </details>
              )}
            </div>
          )}
        </div>
        </div>

        <div className="space-y-4 lg:col-span-2">
          {selectedVersion && selectedVersion.status === "built" && selectedVersion.content ? (
            <ResumeVersionViewer version={selectedVersion} />
          ) : analysis && analysis.status === "analyzed" && analysis.report ? (
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
          {selectedVersion && selectedVersion.status === "built" && selectedVersion.content_text && (
            <div className="rounded-lg border p-4 dark:border-gray-700">
              <details>
                <summary className="cursor-pointer text-xs font-medium opacity-50 hover:opacity-75">
                  Plain Text Render
                </summary>
                <pre className="mt-2 max-h-96 overflow-auto whitespace-pre-wrap rounded bg-gray-50 p-3 text-sm dark:bg-gray-800">
                  {selectedVersion.content_text}
                </pre>
              </details>
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

function ResumeVersionViewer({ version }: { version: ResumeVersion }) {
  const content = version.content;
  if (!content) return null;

  return (
    <div className="rounded-lg border p-6 dark:border-gray-700 space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold">Tailored Resume</h3>
          <div className="mt-1 flex items-center gap-2">
            <Badge variant="gray">v{version.version_no}</Badge>
            <span className="text-xs opacity-50">
              via {version.provider} / {version.model} &middot; prompt {version.prompt_version}
            </span>
          </div>
        </div>
      </div>

      {content.summary && (
        <div>
          <h4 className="text-sm font-semibold opacity-70">Summary</h4>
          <p className="mt-1 text-sm leading-relaxed">{content.summary}</p>
        </div>
      )}

      {(content.sections?.length ?? 0) > 0 && content.sections!.map((section, i) => (
        <div key={i}>
          <h4 className="mb-2 text-sm font-semibold opacity-70">{section.name}</h4>
          <ul className="list-disc space-y-1 pl-5 text-sm">
            {section.items.map((item, j) => (
              <li key={j}>{item}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
