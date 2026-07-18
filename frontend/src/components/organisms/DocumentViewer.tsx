"use client";

import { useEffect } from "react";
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
  useEffect(() => {
    if (!doc) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [doc, onClose]);

  if (!doc) return null;

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
        <div className="flex-1 space-y-3 overflow-y-auto p-4">
          {(!doc.chunks || doc.chunks.length === 0) && (
            <p className="text-sm opacity-50">
              No extracted content available for this document.
            </p>
          )}
          {doc.chunks?.map((chunk) => (
            <div key={chunk.id} className="rounded border p-3 dark:border-gray-700">
              <p className="mb-1 text-xs font-medium opacity-50">
                Chunk {chunk.chunk_index + 1}
              </p>
              <p className="whitespace-pre-wrap text-sm">{chunk.text_content}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
