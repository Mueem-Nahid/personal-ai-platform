"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Badge } from "@/components/atoms/Badge";
import { Button } from "@/components/atoms/Button";
import { RenderResumeDialog } from "@/components/organisms/RenderResumeDialog";
import { ResumeContentEditor } from "@/components/organisms/ResumeContentEditor";
import { api } from "@/lib/api-client";
import type { PdfImportResult, ResumeTemplate, TemplateFormat } from "@/lib/types";

const FORMAT_STUBS: Record<string, string> = {
  html: `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{{ profile.full_name }}</title></head>
<body>
  <h1>{{ profile.full_name }}</h1>
  {% if profile.title %}<p>{{ profile.title }}</p>{% endif %}
  {% if content.summary %}<h2>Summary</h2><p>{{ content.summary }}</p>{% endif %}
  {% for section in content.sections %}
  <h2>{{ section.name }}</h2>
  <ul>{% for item in section.items %}<li>{{ item }}</li>{% endfor %}</ul>
  {% endfor %}
</body>
</html>
`,
  typst: `#set page(paper: "a4", margin: 2cm)
#text(size: 18pt, weight: "bold")[{{ profile.full_name|typst }}]
{% if profile.title %}#text(size: 11pt)[{{ profile.title|typst }}]{% endif %}

{% if content.summary %}
= Summary
{{ content.summary|typst }}
{% endif %}

{% for section in content.sections %}
= {{ section.name|typst }}
{% for item in section.items %}
- {{ item|typst }}
{% endfor %}
{% endfor %}
`,
  latex: `\\documentclass[11pt]{article}
\\usepackage[margin=2cm]{geometry}
\\begin{document}
\\begin{center}{\\Large \\textbf{${"{{ profile.full_name|latex }}"}}}\\end{center}
{% if profile.title %}\\begin{center}{{ profile.title|latex }}\\end{center}{% endif %}
{% if content.summary %}\\section*{Summary}{{ content.summary|latex }}{% endif %}
{% for section in content.sections %}\\section*{ {{ section.name|latex }} }
\\begin{itemize}
{% for item in section.items %}\\item {{ item|latex }}
{% endfor %}\\end{itemize}
{% endfor %}
\\end{document}
`,
  docx: "",
};

interface TemplateManagerProps {
  profileId?: string;
}

export function TemplateManager({ profileId }: TemplateManagerProps) {
  const [templates, setTemplates] = useState<ResumeTemplate[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<ResumeTemplate | null>(null);
  const [creating, setCreating] = useState(false);
  const [importResult, setImportResult] = useState<PdfImportResult | null>(null);
  const [importing, setImporting] = useState(false);
  const [showRenderDialog, setShowRenderDialog] = useState(false);
  const importInputRef = useRef<HTMLInputElement | null>(null);

  const load = useCallback(async () => {
    try {
      const list = await api.listTemplates(profileId);
      setTemplates(list.templates);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load templates");
    } finally {
      setLoading(false);
    }
  }, [profileId]);

  useEffect(() => {
    setLoading(true);
    load();
  }, [load]);

  const handleSetDefault = async (template: ResumeTemplate) => {
    try {
      await api.setDefaultTemplate(template.id, profileId);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to set default");
    }
  };

  const handleDelete = async (template: ResumeTemplate) => {
    try {
      await api.deleteTemplate(template.id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete template");
    }
  };

  const handleImportFile = async (file: File) => {
    setImporting(true);
    setError(null);
    try {
      const result = await api.importResumePdf(file);
      setImportResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Import failed");
    } finally {
      setImporting(false);
    }
  };

  if (loading) {
    return <p className="text-sm opacity-50">Loading templates...</p>;
  }

  return (
    <div className="space-y-6">
      {error && (
        <p className="rounded border border-red-200 bg-red-50 p-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-400">
          {error}
        </p>
      )}

      <div className="rounded-lg border p-4 dark:border-gray-700">
        <h3 className="mb-2 text-sm font-semibold opacity-70">Import Resume PDF</h3>
        <p className="mb-3 text-xs opacity-50">
          Extract a resume PDF into editable sections, tweak it, then render through any template.
        </p>
        <input
          ref={importInputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleImportFile(file);
            e.target.value = "";
          }}
        />
        <Button variant="secondary" size="sm" onClick={() => importInputRef.current?.click()} disabled={importing}>
          {importing ? "Extracting..." : "Choose PDF..."}
        </Button>
        {importResult && (
          <div className="mt-4 space-y-3">
            {(importResult.name || importResult.contact) && (
              <p className="text-xs opacity-60">
                Detected: <span className="font-medium">{importResult.name ?? "Unknown name"}</span>
                {importResult.title ? ` — ${importResult.title}` : ""}
                {importResult.contact ? ` · ${importResult.contact}` : ""}
              </p>
            )}
            <ResumeContentEditor
              initial={importResult.content}
              onCancel={() => setImportResult(null)}
              saveLabel="Save & preview"
              onSave={async (content) => {
                setImportResult({ ...importResult, content });
                setShowRenderDialog(true);
              }}
            />
          </div>
        )}
      </div>

      <div className="rounded-lg border p-4 dark:border-gray-700">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold opacity-70">Resume Templates</h3>
          <Button variant="ghost" size="sm" onClick={() => setCreating(!creating)}>
            {creating ? "Cancel" : "+ New template"}
          </Button>
        </div>

        {creating && (
          <NewTemplateForm
            profileId={profileId}
            onCreated={async () => {
              setCreating(false);
              await load();
            }}
            onCancel={() => setCreating(false)}
          />
        )}

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {templates.map((template) => (
            <div key={template.id} className="rounded-lg border p-3 dark:border-gray-700">
              <div className="flex items-center gap-2">
                <span className="font-medium">{template.name}</span>
                <Badge variant="gray">{template.format}</Badge>
                {template.is_default && <Badge variant="yellow">default</Badge>}
                {template.is_builtin && <Badge variant="blue">built-in</Badge>}
              </div>
              {template.description && (
                <p className="mt-1 text-xs opacity-50">{template.description}</p>
              )}
              <div className="mt-2 flex flex-wrap gap-2">
                <Button variant="ghost" size="sm" onClick={() => setEditing(template)}>
                  Edit
                </Button>
                {!template.is_default && (
                  <Button variant="ghost" size="sm" onClick={() => handleSetDefault(template)}>
                    Set default
                  </Button>
                )}
                {!template.is_builtin && (
                  <Button variant="danger" size="sm" onClick={() => handleDelete(template)}>
                    Delete
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {editing && (
        <TemplateEditorPanel
          template={editing}
          onSaved={async () => {
            setEditing(null);
            await load();
          }}
          onCancel={() => setEditing(null)}
        />
      )}

      {showRenderDialog && importResult && (
        <RenderResumeDialog
          profileId={profileId ?? ""}
          content={importResult.content}
          onClose={() => setShowRenderDialog(false)}
        />
      )}
    </div>
  );
}

function NewTemplateForm({
  profileId,
  onCreated,
  onCancel,
}: {
  profileId?: string;
  onCreated: () => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState("");
  const [format, setFormat] = useState<TemplateFormat>("html");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.createTemplate({
        profile_id: profileId ?? null,
        name,
        format,
        source_text: FORMAT_STUBS[format] ?? null,
      });
      onCreated();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create template");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mb-4 space-y-2 rounded-lg border p-3 dark:border-gray-700">
      {error && <p className="text-xs text-red-600 dark:text-red-400">{error}</p>}
      <div className="flex gap-2">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Template name"
          className="flex-1 rounded border px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
        />
        <select
          value={format}
          onChange={(e) => setFormat(e.target.value as TemplateFormat)}
          className="rounded border px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
        >
          <option value="html">HTML</option>
          <option value="typst">Typst</option>
          <option value="latex">LaTeX</option>
          <option value="docx">DOCX</option>
        </select>
      </div>
      <p className="text-xs opacity-50">
        {format === "docx"
          ? "Generates a Word document from resume content (no template source needed)."
          : format === "latex"
            ? "Requires a TeX distribution in the backend image (disabled by default)."
            : "A starter template will be created — edit it below."}
      </p>
      <div className="flex gap-2">
        <Button variant="primary" size="sm" onClick={handleCreate} disabled={saving || !name.trim()}>
          {saving ? "Creating..." : "Create"}
        </Button>
        <Button variant="ghost" size="sm" onClick={onCancel} disabled={saving}>
          Cancel
        </Button>
      </div>
    </div>
  );
}

function TemplateEditorPanel({
  template,
  onSaved,
  onCancel,
}: {
  template: ResumeTemplate;
  onSaved: () => void;
  onCancel: () => void;
}) {
  const [source, setSource] = useState(template.source_text ?? "");
  const [styles, setStyles] = useState(template.styles_text ?? "");
  const [saving, setSaving] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isTextTemplate = template.format !== "docx";

  const handlePreview = async () => {
    setPreviewing(true);
    setError(null);
    try {
      const blob = await api.previewTemplate({
        format: template.format,
        source_text: source,
        styles_text: styles || null,
      });
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(URL.createObjectURL(blob));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Preview failed");
    } finally {
      setPreviewing(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.updateTemplate(template.id, { source_text: source, styles_text: styles || null });
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="rounded-lg border p-4 dark:border-gray-700">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold opacity-70">
          Editing: {template.name} <Badge variant="gray">{template.format}</Badge>
        </h3>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={handlePreview} disabled={previewing || !isTextTemplate}>
            {previewing ? "Rendering..." : "Preview"}
          </Button>
          <Button variant="primary" size="sm" onClick={handleSave} disabled={saving || !isTextTemplate}>
            {saving ? "Saving..." : "Save"}
          </Button>
          <Button variant="ghost" size="sm" onClick={onCancel} disabled={saving}>
            Close
          </Button>
        </div>
      </div>

      {error && (
        <p className="mb-3 rounded border border-red-200 bg-red-50 p-2 text-xs text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-400">
          {error}
        </p>
      )}

      {!isTextTemplate ? (
        <p className="text-xs opacity-50">
          DOCX builder templates have no editable source — content is generated from the resume.
        </p>
      ) : (
        <div className={template.format === "html" ? "grid grid-cols-1 gap-3 lg:grid-cols-2" : ""}>
          <div>
            <label className="mb-1 block text-xs font-medium opacity-60">
              Template source ({template.format})
            </label>
            <textarea
              value={source}
              onChange={(e) => setSource(e.target.value)}
              rows={18}
              spellCheck={false}
              className="w-full rounded border p-2 font-mono text-xs dark:border-gray-600 dark:bg-gray-800"
            />
            {template.format === "html" && (
              <div className="mt-3">
                <label className="mb-1 block text-xs font-medium opacity-60">Styles (CSS)</label>
                <textarea
                  value={styles}
                  onChange={(e) => setStyles(e.target.value)}
                  rows={8}
                  spellCheck={false}
                  className="w-full rounded border p-2 font-mono text-xs dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
            )}
          </div>
          {template.format === "html" && (
            <div>
              <label className="mb-1 block text-xs font-medium opacity-60">Preview</label>
              {previewUrl ? (
                <iframe
                  src={previewUrl}
                  title="Template preview"
                  className="h-[480px] w-full rounded border dark:border-gray-600"
                />
              ) : (
                <div className="flex h-[480px] items-center justify-center rounded border text-xs opacity-40 dark:border-gray-600">
                  Click &quot;Preview&quot; to render
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {template.format !== "html" && previewUrl && (
        <iframe
          src={previewUrl}
          title="Template preview"
          className="mt-3 h-[480px] w-full rounded border dark:border-gray-600"
        />
      )}
    </div>
  );
}
