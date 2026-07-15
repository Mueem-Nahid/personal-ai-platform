import type { DocumentOut } from "@/lib/types";
import { Badge } from "@/components/atoms/Badge";
import { Button } from "@/components/atoms/Button";

const statusVariant: Record<string, "gray" | "yellow" | "green" | "red"> = {
  uploaded: "gray",
  processing: "yellow",
  processed: "green",
  failed: "red",
};

function formatSize(bytes: number | null | undefined): string {
  if (bytes == null) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface DocumentCardProps {
  document: DocumentOut;
  onDelete: (id: string) => void;
  onView: (id: string) => void;
}

export function DocumentCard({ document: doc, onDelete, onView }: DocumentCardProps) {
  return (
    <div className="flex items-center justify-between rounded-lg border p-4 dark:border-gray-700">
      <div className="flex items-center gap-3">
        <div>
          <p className="font-medium">{doc.filename}</p>
          <div className="mt-1 flex items-center gap-2 text-xs opacity-60">
            <span>{doc.file_type.toUpperCase()}</span>
            <span>{formatSize(doc.file_size_bytes)}</span>
            <span>{doc.chunk_count ?? 0} chunks</span>
          </div>
        </div>
        <Badge variant={statusVariant[doc.status] ?? "gray"}>{doc.status}</Badge>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={() => onView(doc.id)}>
          View
        </Button>
        <Button variant="danger" size="sm" onClick={() => onDelete(doc.id)}>
          Delete
        </Button>
      </div>
    </div>
  );
}
