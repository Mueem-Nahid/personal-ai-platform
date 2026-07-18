"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/atoms/Button";
import { Textarea } from "@/components/atoms/Textarea";
import { Input } from "@/components/atoms/Input";

type Tab = "text" | "url" | "pdf";

interface JobParserProps {
  onParseUrl: (url: string) => Promise<void>;
  onParseText: (text: string) => Promise<void>;
  onParsePdf: (file: File) => Promise<void>;
  disabled?: boolean;
}

export function JobParser({ onParseUrl, onParseText, onParsePdf, disabled }: JobParserProps) {
  const [tab, setTab] = useState<Tab>("text");
  const [url, setUrl] = useState("");
  const [text, setText] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async () => {
    if (tab === "url" && url.trim()) {
      await onParseUrl(url.trim());
      setUrl("");
    } else if (tab === "text" && text.trim().length >= 50) {
      await onParseText(text.trim());
      setText("");
    }
  };

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await onParsePdf(file);
    e.target.value = "";
  };

  const canSubmit =
    (tab === "url" && url.trim()) ||
    (tab === "text" && text.trim().length >= 50);

  const tabs: { key: Tab; label: string }[] = [
    { key: "text", label: "Paste Text" },
    { key: "url", label: "URL" },
    { key: "pdf", label: "PDF" },
  ];

  return (
    <div className="space-y-4">
      <div className="flex gap-1 rounded-lg border p-1 dark:border-gray-700">
        {tabs.map((t) => (
          <button
            key={t.key}
            type="button"
            className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              tab === t.key
                ? "bg-blue-600 text-white"
                : "opacity-50 hover:opacity-75"
            }`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "text" && (
        <Textarea
          placeholder="Paste a job posting here (minimum 50 characters)..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={8}
          disabled={disabled}
        />
      )}

      {tab === "url" && (
        <Input
          placeholder="https://careers.example.com/jobs/123"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={disabled}
        />
      )}

      {tab === "pdf" && (
        <div className="space-y-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={handleFile}
            disabled={disabled}
          />
          <Button
            type="button"
            variant="primary"
            disabled={disabled}
            onClick={() => fileInputRef.current?.click()}
          >
            {disabled ? "Parsing..." : "Upload PDF"}
          </Button>
        </div>
      )}

      {tab !== "pdf" && (
        <Button
          type="button"
          variant="primary"
          disabled={!canSubmit || disabled}
          onClick={handleSubmit}
        >
          {disabled ? "Parsing..." : "Parse Job Post"}
        </Button>
      )}
    </div>
  );
}
