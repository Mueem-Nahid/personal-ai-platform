"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import type { JobPost } from "@/lib/types";
import { api } from "@/lib/api-client";
import { ErrorBanner } from "@/components/organisms/ErrorBanner";
import { JobParser } from "@/components/organisms/JobParser";
import { JobViewer } from "@/components/organisms/JobViewer";
import { JobCard } from "@/components/molecules/JobCard";
import { PageHeader } from "@/components/organisms/PageHeader";

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobPost[]>([]);
  const [loading, setLoading] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [parsingMessage, setParsingMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [viewingJob, setViewingJob] = useState<JobPost | null>(null);
  const isMounted = useRef(true);

  const POLL_TIMEOUT = 360000; // 6 minutes (must exceed LLM timeout of 300s)
  const POLL_INTERVAL = 3000; // 3 seconds

  useEffect(() => {
    return () => { isMounted.current = false; };
  }, []);

  const loadJobs = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.listJobs();
      if (isMounted.current) setJobs(response.jobs);
    } catch (e) {
      if (isMounted.current) setError(e instanceof Error ? e.message : "Failed to load jobs");
    } finally {
      if (isMounted.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  const pollJobStatus = async (jobId: string): Promise<void> => {
    const start = Date.now();
    let attempts = 0;
    while (isMounted.current) {
      if (Date.now() - start > POLL_TIMEOUT) {
        throw new Error("Parsing timed out — check the job list for results");
      }
      await new Promise((r) => setTimeout(r, POLL_INTERVAL));
      try {
        const job = await api.getJob(jobId);
        if (job.status !== "parsing") {
          setParsingMessage(`Done — ${job.status === "parsed" ? "parsed successfully" : "parsing failed"}`);
          return;
        }
        attempts += 1;
        if (isMounted.current) {
          setParsingMessage(`Parsing${".".repeat((attempts % 3) + 1)}`);
        }
      } catch (e) {
        if (isMounted.current) {
          console.warn("Poll attempt %d failed:", attempts, e);
        }
      }
    }
  };

  const handleParseUrl = async (url: string) => {
    setParsing(true);
    setParsingMessage("Fetching job page...");
    setError(null);
    try {
      const { job_id } = await api.parseJobUrl(url);
      await pollJobStatus(job_id);
      await loadJobs();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to parse job URL");
    } finally {
      if (isMounted.current) {
        setParsing(false);
        setParsingMessage(null);
      }
    }
  };

  const handleParseText = async (text: string) => {
    setParsing(true);
    setParsingMessage("Parsing...");
    setError(null);
    try {
      const { job_id } = await api.parseJobText(text);
      await pollJobStatus(job_id);
      await loadJobs();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to parse job text");
    } finally {
      if (isMounted.current) {
        setParsing(false);
        setParsingMessage(null);
      }
    }
  };

  const handleParsePdf = async (file: File) => {
    setParsing(true);
    setParsingMessage("Parsing PDF...");
    setError(null);
    try {
      const { job_id } = await api.parseJobPdf(file);
      await pollJobStatus(job_id);
      await loadJobs();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to parse PDF");
    } finally {
      if (isMounted.current) {
        setParsing(false);
        setParsingMessage(null);
      }
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
      <div>
        <PageHeader title="Jobs" backHref="/" />

      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <JobParser
        onParseUrl={handleParseUrl}
        onParseText={handleParseText}
        onParsePdf={handleParsePdf}
        disabled={parsing}
      />

      {parsingMessage && (
        <p className="text-sm text-blue-600 dark:text-blue-400">{parsingMessage}</p>
      )}

      {loading && <p className="text-sm opacity-50">Loading jobs...</p>}

      <div className="space-y-2">
        {jobs.map((job) => (
          <JobCard key={job.id} job={job} onView={handleView} onDelete={handleDelete} />
        ))}
        {!loading && jobs.length === 0 && (
          <p className="text-sm opacity-50">
            No jobs parsed yet. Paste a job posting above to get started.
          </p>
        )}
      </div>

      <JobViewer job={viewingJob} onClose={() => setViewingJob(null)} />
    </div>
  );
}
