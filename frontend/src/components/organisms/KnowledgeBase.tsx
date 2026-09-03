"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import type { DocumentOut, MasterResume } from "@/lib/types";
import { api } from "@/lib/api-client";
import { Button } from "@/components/atoms/Button";
import { DocumentCard } from "@/components/molecules/DocumentCard";
import { DocumentViewer } from "@/components/organisms/DocumentViewer";
import { ErrorBanner } from "@/components/organisms/ErrorBanner";

interface KnowledgeBaseProps {
  profileId: string;
}

export function KnowledgeBase({ profileId }: KnowledgeBaseProps) {
  const [documents, setDocuments] = useState<DocumentOut[]>([]);
  const [masterResumes, setMasterResumes] = useState<MasterResume[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [viewingDoc, setViewingDoc] = useState<DocumentOut | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadDocuments = useCallback(async () => {
    try {
      setLoading(true);
      const [docsResp, mastersResp] = await Promise.all([
        api.listDocuments(profileId),
        api.listMasterResumes(profileId),
      ]);
      setDocuments(docsResp.documents);
      setMasterResumes(mastersResp.resumes);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load documents");
    } finally {
      setLoading(false);
    }
  }, [profileId]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const masterByDocId = new Map<string, MasterResume>(
    masterResumes.map((m) => [m.document_id, m])
  );

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setUploading(true);
      await api.uploadDocument(profileId, file);
      await loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleView = async (documentId: string) => {
    try {
      const doc = await api.getDocument(profileId, documentId);
      setViewingDoc(doc);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load document");
    }
  };

  const handleDelete = async (documentId: string) => {
    try {
      await api.deleteDocument(profileId, documentId);
      setDocuments((prev) => prev.filter((d) => d.id !== documentId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  };

  const handleDesignateMaster = async (documentId: string) => {
    try {
      await api.designateMasterResume(profileId, documentId, true);
      await loadDocuments();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to set as master resume");
    }
  };

  return (
    <div className="space-y-4">
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <div className="flex items-center gap-4">
        <Button
          type="button"
          variant="primary"
          size="md"
          disabled={uploading}
          onClick={() => fileInputRef.current?.click()}
        >
          {uploading ? "Uploading..." : "Upload Document"}
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.docx,.doc,.txt,.md"
          onChange={handleUpload}
          disabled={uploading}
        />
        <Button variant="secondary" size="md" onClick={loadDocuments} disabled={loading}>
          Refresh
        </Button>
      </div>

      {loading && <p className="text-sm opacity-50">Loading documents...</p>}

      <div className="space-y-2">
        {documents.map((doc) => {
          const master = masterByDocId.get(doc.id);
          return (
            <DocumentCard
              key={doc.id}
              document={doc}
              onDelete={handleDelete}
              onView={handleView}
              isMasterResume={!!master && master.status === "active"}
              isDefaultMaster={!!master && master.is_default}
              onDesignateMaster={() => handleDesignateMaster(doc.id)}
            />
          );
        })}
        {!loading && documents.length === 0 && (
          <p className="text-sm opacity-50">
            No documents yet. Upload a CV, certificate, or project document to build your knowledge base.
          </p>
        )}
      </div>

      <DocumentViewer document={viewingDoc} onClose={() => setViewingDoc(null)} />
    </div>
  );
}
