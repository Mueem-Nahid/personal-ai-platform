"use client";

import { useState } from "react";
import { Button } from "@/components/atoms/Button";
import type { ResumeContent, ResumeSection } from "@/lib/types";

interface ResumeContentEditorProps {
  initial: ResumeContent;
  onSave: (content: ResumeContent) => Promise<void> | void;
  onCancel: () => void;
  saveLabel?: string;
}

export function ResumeContentEditor({
  initial,
  onSave,
  onCancel,
  saveLabel = "Save",
}: ResumeContentEditorProps) {
  const [summary, setSummary] = useState(initial.summary ?? "");
  const [sections, setSections] = useState<ResumeSection[]>(
    (initial.sections ?? []).map((s) => ({ name: s.name, items: [...s.items] })),
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const setSection = (index: number, patch: Partial<ResumeSection>) => {
    setSections((prev) => prev.map((s, i) => (i === index ? { ...s, ...patch } : s)));
  };

  const moveSection = (index: number, direction: -1 | 1) => {
    const target = index + direction;
    if (target < 0 || target >= sections.length) return;
    setSections((prev) => {
      const next = [...prev];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await onSave({
        summary: summary.trim() || null,
        sections: sections
          .map((s) => ({ name: s.name.trim(), items: s.items.map((i) => i.trim()).filter(Boolean) }))
          .filter((s) => s.name && s.items.length > 0),
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="mb-1 block text-xs font-medium opacity-60">Summary</label>
        <textarea
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          rows={3}
          className="w-full rounded border px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
          placeholder="Professional summary (optional)"
        />
      </div>

      {sections.map((section, si) => (
        <div key={si} className="rounded-lg border p-3 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <input
              value={section.name}
              onChange={(e) => setSection(si, { name: e.target.value })}
              className="flex-1 rounded border px-2 py-1 text-sm font-medium dark:border-gray-600 dark:bg-gray-800"
              placeholder="Section name"
            />
            <Button variant="ghost" size="sm" onClick={() => moveSection(si, -1)} disabled={si === 0}>
              ↑
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => moveSection(si, 1)}
              disabled={si === sections.length - 1}
            >
              ↓
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => setSections((prev) => prev.filter((_, i) => i !== si))}
            >
              Remove
            </Button>
          </div>
          <div className="mt-2 space-y-2">
            {section.items.map((item, ii) => (
              <div key={ii} className="flex items-start gap-2">
                <span className="mt-2 text-xs opacity-40">•</span>
                <textarea
                  value={item}
                  onChange={(e) =>
                    setSection(si, {
                      items: section.items.map((it, j) => (j === ii ? e.target.value : it)),
                    })
                  }
                  rows={2}
                  className="flex-1 rounded border px-2 py-1 text-sm dark:border-gray-600 dark:bg-gray-800"
                />
                <Button
                  variant="danger"
                  size="sm"
                  className="mt-1"
                  onClick={() =>
                    setSection(si, { items: section.items.filter((_, j) => j !== ii) })
                  }
                >
                  ×
                </Button>
              </div>
            ))}
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="mt-2"
            onClick={() => setSection(si, { items: [...section.items, ""] })}
          >
            + Add bullet
          </Button>
        </div>
      ))}

      <Button
        variant="secondary"
        size="sm"
        onClick={() => setSections((prev) => [...prev, { name: "", items: [""] }])}
      >
        + Add section
      </Button>

      {error && (
        <p className="rounded border border-red-200 bg-red-50 p-2 text-xs text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-400">
          {error}
        </p>
      )}

      <div className="flex gap-2 border-t pt-3 dark:border-gray-700">
        <Button variant="primary" size="sm" onClick={handleSave} disabled={saving}>
          {saving ? "Saving..." : saveLabel}
        </Button>
        <Button variant="ghost" size="sm" onClick={onCancel} disabled={saving}>
          Cancel
        </Button>
      </div>
    </div>
  );
}
