"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Badge } from "@/components/atoms/Badge";
import { Button } from "@/components/atoms/Button";
import { api } from "@/lib/api-client";
import type {
  OutputFormat,
  RenderFormatCapability,
  ResumeContent,
  ResumeTemplate,
} from "@/lib/types";

interface RenderResumeDialogProps {
  profileId: string;
  resumeVersionId?: string;
  content?: ResumeContent | null;
  onClose: () => void;
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function RenderResumeDialog({
  profileId,
  resumeVersionId,
  content,
  onClose,
}: RenderResumeDialogProps) {
  const [templates, setTemplates] = useState<ResumeTemplate[]>([]);
  const [capabilities, setCapabilities] = useState<RenderFormatCapability[]>([]);
  const [templateId, setTemplateId] = useState("");
  const [outputFormat, setOutputFormat] = useState<OutputFormat>("pdf");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [rendering, setRendering] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [templateList, formats] = await Promise.all([
          api.listTemplates(profileId),
          api.getRenderFormats(),
        ]);
        setTemplates(templateList.templates);
        setCapabilities(formats.formats);
        const preferred =
          templateList.templates.find((t) => t.is_default && t.profile_id === profileId) ??
          templateList.templates.find((t) => t.is_default) ??
          templateList.templates[0];
        if (preferred) setTemplateId(preferred.id);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load templates");
      }
    })();
  }, [profileId]);

  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  const selectedTemplate = useMemo(
    () => templates.find((t) => t.id === templateId) ?? null,
    [templates, templateId],
  );

  const availableOutputs = useMemo(() => {
    if (!selectedTemplate) return [] as { value: OutputFormat; label: string }[];
    return capabilities
      .filter((c) => c.format === selectedTemplate.format && c.available)
      .map((c) => ({
        value: c.output as OutputFormat,
        label: `${c.output.toUpperCase()} (${c.engine})`,
      }));
  }, [capabilities, selectedTemplate]);

  useEffect(() => {
    if (availableOutputs.length > 0 && !availableOutputs.some((o) => o.value === outputFormat)) {
      setOutputFormat(availableOutputs[0].value);
    }
  }, [availableOutputs, outputFormat]);

  const pollAndDownload = useCallback(
    (jobId: string, attempts = 0) => {
      if (attempts > 30) {
        setRendering(false);
        setError("Render timed out");
        if (pollingRef.current) clearInterval(pollingRef.current);
        return;
      }
      api
        .getRenderJob(jobId)
        .then(async (job) => {
          if (job.status === "done") {
            if (pollingRef.current) clearInterval(pollingRef.current);
            const { blob, filename } = await api.downloadRenderJob(jobId);
            triggerDownload(blob, filename ?? `resume.${job.output_format}`);
            setRendering(false);
            setStatus(`Downloaded ${filename ?? "resume"}`);
          } else if (job.status === "failed") {
            if (pollingRef.current) clearInterval(pollingRef.current);
            setRendering(false);
            setError(job.error ?? "Render failed");
          } else {
            setStatus(`Rendering${".".repeat((attempts % 3) + 1)}`);
          }
        })
        .catch((e: unknown) => {
          if (pollingRef.current) clearInterval(pollingRef.current);
          setRendering(false);
          setError(e instanceof Error ? e.message : "Render polling failed");
        });
    },
    [],
  );

  const handleRender = async () => {
    setError(null);
    setStatus("Starting render...");
    setRendering(true);
    try {
      const { render_job_id } = await api.startRender({
        profile_id: profileId,
        template_id: templateId,
        output_format: outputFormat,
        resume_version_id: resumeVersionId ?? null,
        content: resumeVersionId ? undefined : (content ?? undefined),
      });
      let attempts = 0;
      pollingRef.current = setInterval(() => {
        attempts += 1;
        pollAndDownload(render_job_id, attempts);
      }, 1500);
    } catch (e) {
      setRendering(false);
      setStatus(null);
      setError(e instanceof Error ? e.message : "Render failed to start");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-lg border bg-white p-5 dark:border-gray-700 dark:bg-gray-900">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">Render Resume</h3>
          <Button variant="ghost" size="sm" onClick={onClose} disabled={rendering}>
            ✕
          </Button>
        </div>

        {error && (
          <p className="mb-3 rounded border border-red-200 bg-red-50 p-2 text-xs text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-400">
            {error}
          </p>
        )}

        <label className="mb-1 block text-xs font-medium opacity-60">Template</label>
        <select
          value={templateId}
          onChange={(e) => setTemplateId(e.target.value)}
          className="mb-3 w-full rounded border px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
          disabled={rendering}
        >
          {templates.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name} ({t.format}){t.is_default ? " ★" : ""}
            </option>
          ))}
        </select>

        <label className="mb-1 block text-xs font-medium opacity-60">Output format</label>
        {availableOutputs.length === 0 ? (
          <p className="mb-3 text-xs opacity-50">No available outputs for this template.</p>
        ) : (
          <select
            value={outputFormat}
            onChange={(e) => setOutputFormat(e.target.value as OutputFormat)}
            className="mb-3 w-full rounded border px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
            disabled={rendering}
          >
            {availableOutputs.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        )}

        {status && (
          <div className="mb-3 flex items-center gap-2">
            <Badge variant={rendering ? "yellow" : "green"}>{status}</Badge>
          </div>
        )}

        <div className="flex justify-end gap-2 border-t pt-3 dark:border-gray-700">
          <Button variant="ghost" size="sm" onClick={onClose} disabled={rendering}>
            Close
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleRender}
            disabled={rendering || !templateId || availableOutputs.length === 0}
          >
            {rendering ? "Rendering..." : `Render ${outputFormat.toUpperCase()}`}
          </Button>
        </div>
      </div>
    </div>
  );
}
