"use client";

import { useEffect } from "react";
import type { JobPost } from "@/lib/types";
import { Badge } from "@/components/atoms/Badge";
import { Button } from "@/components/atoms/Button";

interface JobViewerProps {
  job: JobPost | null;
  onClose: () => void;
}

export function JobViewer({ job, onClose }: JobViewerProps) {
  useEffect(() => {
    if (!job) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [job, onClose]);

  if (!job) return null;

  const fields = job.parsed_fields;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <div
        className="flex max-h-[80vh] w-full max-w-2xl flex-col rounded-lg bg-white shadow-xl dark:bg-gray-900"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 border-b p-4 dark:border-gray-700">
          <div>
            <h2 className="text-lg font-semibold">
              {fields?.title || job.title || "Untitled"}
            </h2>
            <p className="text-sm opacity-70">
              {fields?.company || job.company || "Unknown company"}
              {fields?.location ? ` · ${fields.location}` : ""}
            </p>
            {fields?.salary && (
              <p className="mt-1 text-sm font-medium text-green-600 dark:text-green-400">
                {fields.salary}
              </p>
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {fields?.requirements && fields.requirements.length > 0 && (
            <Section title="Requirements">
              <BulletList items={fields.requirements} />
            </Section>
          )}

          {fields?.responsibilities && fields.responsibilities.length > 0 && (
            <Section title="Responsibilities">
              <BulletList items={fields.responsibilities} />
            </Section>
          )}

          {fields?.skills && fields.skills.length > 0 && (
            <Section title="Skills">
              <div className="flex flex-wrap gap-1">
                {fields.skills.map((s) => (
                  <Badge key={s} variant="gray">{s}</Badge>
                ))}
              </div>
            </Section>
          )}

          {fields?.tech_stack && fields.tech_stack.length > 0 && (
            <Section title="Tech Stack">
              <div className="flex flex-wrap gap-1">
                {fields.tech_stack.map((t) => (
                  <Badge key={t} variant="gray">{t}</Badge>
                ))}
              </div>
            </Section>
          )}

          {fields?.experience && (
            <Section title="Experience">
              <p className="text-sm">{fields.experience}</p>
            </Section>
          )}

          {fields?.employment_type && (
            <Section title="Employment Type">
              <p className="text-sm">{fields.employment_type}</p>
            </Section>
          )}

          {job.raw_text && (
            <details className="border-t pt-4 dark:border-gray-700">
              <summary className="cursor-pointer text-xs font-medium opacity-50 hover:opacity-75">
                Raw Text
              </summary>
              <p className="mt-2 whitespace-pre-wrap text-xs opacity-60">
                {job.raw_text.slice(0, 3000)}
                {job.raw_text.length > 3000 ? "..." : ""}
              </p>
            </details>
          )}
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold opacity-70">{title}</h3>
      {children}
    </div>
  );
}

function BulletList({ items }: { items: string[] }) {
  return (
    <ul className="list-disc space-y-1 pl-5 text-sm">
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  );
}
