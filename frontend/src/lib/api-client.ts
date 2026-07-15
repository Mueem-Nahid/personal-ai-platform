import type {
  Profile,
  ProfileCreate,
  ProfileUpdate,
  Experience,
  Project,
  Education,
  Skill,
  Certificate,
  Achievement,
  Publication,
  Language,
  DocumentOut,
  DocumentListOut,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    cache: "no-store",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${path} failed: ${res.status} ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  // Profile
  listProfiles: () => request<Profile[]>("/profiles"),
  getProfile: (id: string) => request<Profile>(`/profiles/${id}`),
  createProfile: (data: ProfileCreate) =>
    request<Profile>("/profiles", { method: "POST", body: JSON.stringify(data) }),
  updateProfile: (id: string, data: ProfileUpdate) =>
    request<Profile>(`/profiles/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteProfile: (id: string) =>
    request<void>(`/profiles/${id}`, { method: "DELETE" }),

  // Experience
  listExperiences: (profileId: string) =>
    request<Experience[]>(`/profiles/${profileId}/experiences`),
  createExperience: (profileId: string, data: Partial<Experience>) =>
    request<Experience>(`/profiles/${profileId}/experiences`, { method: "POST", body: JSON.stringify(data) }),
  updateExperience: (profileId: string, id: string, data: Partial<Experience>) =>
    request<Experience>(`/profiles/${profileId}/experiences/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteExperience: (profileId: string, id: string) =>
    request<void>(`/profiles/${profileId}/experiences/${id}`, { method: "DELETE" }),

  // Skills
  listSkills: (profileId: string) =>
    request<Skill[]>(`/profiles/${profileId}/skills`),
  createSkill: (profileId: string, data: Partial<Skill>) =>
    request<Skill>(`/profiles/${profileId}/skills`, { method: "POST", body: JSON.stringify(data) }),
  updateSkill: (profileId: string, id: string, data: Partial<Skill>) =>
    request<Skill>(`/profiles/${profileId}/skills/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteSkill: (profileId: string, id: string) =>
    request<void>(`/profiles/${profileId}/skills/${id}`, { method: "DELETE" }),

  // Education
  listEducation: (profileId: string) =>
    request<Education[]>(`/profiles/${profileId}/education`),
  createEducation: (profileId: string, data: Partial<Education>) =>
    request<Education>(`/profiles/${profileId}/education`, { method: "POST", body: JSON.stringify(data) }),
  updateEducation: (profileId: string, id: string, data: Partial<Education>) =>
    request<Education>(`/profiles/${profileId}/education/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteEducation: (profileId: string, id: string) =>
    request<void>(`/profiles/${profileId}/education/${id}`, { method: "DELETE" }),

  // Projects
  listProjects: (profileId: string) =>
    request<Project[]>(`/profiles/${profileId}/projects`),
  createProject: (profileId: string, data: Partial<Project>) =>
    request<Project>(`/profiles/${profileId}/projects`, { method: "POST", body: JSON.stringify(data) }),
  updateProject: (profileId: string, id: string, data: Partial<Project>) =>
    request<Project>(`/profiles/${profileId}/projects/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteProject: (profileId: string, id: string) =>
    request<void>(`/profiles/${profileId}/projects/${id}`, { method: "DELETE" }),

  // Certificates
  listCertificates: (profileId: string) =>
    request<Certificate[]>(`/profiles/${profileId}/certificates`),
  createCertificate: (profileId: string, data: Partial<Certificate>) =>
    request<Certificate>(`/profiles/${profileId}/certificates`, { method: "POST", body: JSON.stringify(data) }),
  updateCertificate: (profileId: string, id: string, data: Partial<Certificate>) =>
    request<Certificate>(`/profiles/${profileId}/certificates/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteCertificate: (profileId: string, id: string) =>
    request<void>(`/profiles/${profileId}/certificates/${id}`, { method: "DELETE" }),

  // Languages
  listLanguages: (profileId: string) =>
    request<Language[]>(`/profiles/${profileId}/languages`),
  createLanguage: (profileId: string, data: Partial<Language>) =>
    request<Language>(`/profiles/${profileId}/languages`, { method: "POST", body: JSON.stringify(data) }),
  updateLanguage: (profileId: string, id: string, data: Partial<Language>) =>
    request<Language>(`/profiles/${profileId}/languages/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteLanguage: (profileId: string, id: string) =>
    request<void>(`/profiles/${profileId}/languages/${id}`, { method: "DELETE" }),

  // Knowledge Base
  uploadDocument: async (profileId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${BASE}/profiles/${profileId}/knowledge`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText);
      throw new Error(`Upload failed: ${res.status} ${text}`);
    }
    return res.json() as Promise<DocumentOut>;
  },
  listDocuments: (profileId: string) =>
    request<DocumentListOut>(`/profiles/${profileId}/knowledge`),
  getDocument: (profileId: string, documentId: string) =>
    request<DocumentOut>(`/profiles/${profileId}/knowledge/${documentId}`),
  deleteDocument: (profileId: string, documentId: string) =>
    request<void>(`/profiles/${profileId}/knowledge/${documentId}`, { method: "DELETE" }),
};
