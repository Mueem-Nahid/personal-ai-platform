"use client";

import { useState, useEffect } from "react";
import type { DocumentOut } from "@/lib/types";
import { Badge } from "@/components/atoms/Badge";
import { Button } from "@/components/atoms/Button";

const statusVariant: Record<string, "gray" | "yellow" | "green" | "red"> = {
  uploaded: "gray",
  processing: "yellow",
  processed: "green",
  failed: "red",
};

interface DocumentViewerProps {
  document: DocumentOut | null;
  onClose: () => void;
}

export function DocumentViewer({ document: doc, onClose }: DocumentViewerProps) {
  const [showChunks, setShowChunks] = useState(false);

  useEffect(() => {
    if (!doc) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [doc, onClose]);

  if (!doc) return null;

  const hasFullText = Boolean(doc.extracted_text);
  const hasChunks = doc.chunks && doc.chunks.length > 0;

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
            <h2 className="text-lg font-semibold">{doc.filename}</h2>
            <div className="mt-1 flex items-center gap-2 text-xs opacity-60">
              <span>{doc.file_type.toUpperCase()}</span>
              <span>{doc.chunk_count ?? 0} chunks</span>
              <Badge variant={statusVariant[doc.status] ?? "gray"}>{doc.status}</Badge>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {hasFullText ? (
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{doc.extracted_text}</p>
          ) : hasChunks ? (
            <div className="space-y-3">
              {doc.chunks!.map((chunk) => (
                <div key={chunk.id} className="rounded border p-3 dark:border-gray-700">
                  <p className="mb-1 text-xs font-medium opacity-50">
                    Chunk {chunk.chunk_index + 1}
                  </p>
                  <p className="whitespace-pre-wrap text-sm">{chunk.text_content}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm opacity-50">
              No extracted content available for this document.
            </p>
          )}

          {hasChunks && (
            <details
              className="mt-4 border-t pt-4 dark:border-gray-700"
              open={showChunks}
              onToggle={(e) => setShowChunks((e.target as HTMLDetailsElement).open)}
            >
              <summary className="cursor-pointer text-xs font-medium opacity-50 hover:opacity-75">
                Chunks (debug) &mdash; {doc.chunk_count ?? doc.chunks!.length} segments
              </summary>
              <div className="mt-3 space-y-3">
                {doc.chunks!.map((chunk) => (
                  <div
                    key={chunk.id}
                    className="rounded border border-dashed p-3 dark:border-gray-600"
                  >
                    <p className="mb-1 text-xs font-medium opacity-50">
                      Chunk {chunk.chunk_index + 1}
                    </p>
                    <p className="whitespace-pre-wrap text-xs opacity-70">
                      {chunk.text_content}
                    </p>
                  </div>
                ))}
              </div>
            </details>
          )}
        </div>
      </div>
    </div>
  );
}
