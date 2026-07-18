"use client";

import { useState, useCallback, useEffect } from "react";
import type { JobPost } from "@/lib/types";
import { api } from "@/lib/api-client";
import { PageShell } from "@/components/templates/PageShell";
import { ErrorBanner } from "@/components/organisms/ErrorBanner";
import { JobParser } from "@/components/organisms/JobParser";
import { JobViewer } from "@/components/organisms/JobViewer";
import { JobCard } from "@/components/molecules/JobCard";

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobPost[]>([]);
  const [loading, setLoading] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewingJob, setViewingJob] = useState<JobPost | null>(null);

  const loadJobs = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.listJobs();
      setJobs(response.jobs);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load jobs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  const handleParseUrl = async (url: string) => {
    try {
      setParsing(true);
      setError(null);
      await api.parseJobUrl(url);
      await loadJobs();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to parse job URL");
    } finally {
      setParsing(false);
    }
  };

  const handleParseText = async (text: string) => {
    try {
      setParsing(true);
      setError(null);
      await api.parseJobText(text);
      await loadJobs();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to parse job text");
    } finally {
      setParsing(false);
    }
  };

  const handleParsePdf = async (file: File) => {
    try {
      setParsing(true);
      setError(null);
      await api.parseJobPdf(file);
      await loadJobs();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to parse PDF");
    } finally {
      setParsing(false);
    }
  };

  const handleView = async (jobId: string) => {
    try {
      const job = await api.getJob(jobId);
      setViewingJob(job);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load job");
    }
  };

  const handleDelete = async (jobId: string) => {
    try {
      await api.deleteJob(jobId);
      setJobs((prev) => prev.filter((j) => j.id !== jobId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  };

  return (
    <PageShell>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Jobs</h1>

        <ErrorBanner error={error} onDismiss={() => setError(null)} />

        <JobParser
          onParseUrl={handleParseUrl}
          onParseText={handleParseText}
          onParsePdf={handleParsePdf}
          disabled={parsing}
        />

        {loading && <p className="text-sm opacity-50">Loading jobs...</p>}

        <div className="space-y-2">
          {jobs.map((job) => (
            <JobCard key={job.id} job={job} onView={handleView} onDelete={handleDelete} />
          ))}
          {!loading && jobs.length === 0 && (
            <p className="text-sm opacity-50">No jobs parsed yet. Paste a job posting above to get started.</p>
          )}
        </div>

        <JobViewer job={viewingJob} onClose={() => setViewingJob(null)} />
      </div>
    </PageShell>
  );
}
