export interface Experience {
  id?: string;
  profile_id?: string;
  company: string;
  title: string;
  location?: string | null;
  employment_type?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  current: boolean;
  description?: string | null;
  bullet_points?: string[] | null;
  created_at?: string;
  updated_at?: string;
}

export interface Project {
  id?: string;
  profile_id?: string;
  name: string;
  description?: string | null;
  url?: string | null;
  tech_stack?: string[] | null;
  start_date?: string | null;
  end_date?: string | null;
  bullet_points?: string[] | null;
  created_at?: string;
  updated_at?: string;
}

export interface Education {
  id?: string;
  profile_id?: string;
  institution: string;
  degree?: string | null;
  field_of_study?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  gpa?: string | null;
  description?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface Skill {
  id?: string;
  profile_id?: string;
  name: string;
  category?: string | null;
  proficiency?: string | null;
  years_of_experience?: number | null;
  created_at?: string;
  updated_at?: string;
}

export interface Certificate {
  id?: string;
  profile_id?: string;
  name: string;
  issuer?: string | null;
  issue_date?: string | null;
  expiry_date?: string | null;
  credential_id?: string | null;
  url?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface Achievement {
  id?: string;
  profile_id?: string;
  title: string;
  description?: string | null;
  event_date?: string | null;
  category?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface Publication {
  id?: string;
  profile_id?: string;
  title: string;
  publisher?: string | null;
  event_date?: string | null;
  url?: string | null;
  description?: string | null;
  authors?: string[] | null;
  created_at?: string;
  updated_at?: string;
}

export interface Language {
  id?: string;
  profile_id?: string;
  name: string;
  proficiency?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface Profile {
  id?: string;
  full_name: string;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  title?: string | null;
  summary?: string | null;
  github_url?: string | null;
  linkedin_url?: string | null;
  website?: string | null;
  created_at?: string;
  updated_at?: string;
  experiences?: Experience[];
  projects?: Project[];
  education?: Education[];
  skills?: Skill[];
  certificates?: Certificate[];
  achievements?: Achievement[];
  publications?: Publication[];
  languages?: Language[];
}

export type ProfileCreate = Omit<Profile, "id" | "created_at" | "updated_at">;
export type ProfileUpdate = Partial<Omit<Profile, "id" | "created_at" | "updated_at" | "experiences" | "projects" | "education" | "skills" | "certificates" | "achievements" | "publications" | "languages">>;

export interface DocumentChunk {
  id: string;
  document_id: string;
  profile_id: string;
  chunk_index: number;
  text_content: string;
  qdrant_point_id?: string | null;
  created_at: string;
}

export interface DocumentOut {
  id: string;
  profile_id: string;
  filename: string;
  file_type: string;
  file_size_bytes?: number | null;
  status: string;
  chunk_count?: number | null;
  extracted_text?: string | null;
  extra_metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  chunks?: DocumentChunk[];
}

export interface DocumentListOut {
  documents: DocumentOut[];
  total: number;
}

export interface JobParsedFields {
  title?: string | null;
  company?: string | null;
  location?: string | null;
  salary?: string | null;
  experience?: string | null;
  employment_type?: string | null;
  requirements?: string[];
  responsibilities?: string[];
  skills?: string[];
  keywords?: string[];
  tech_stack?: string[];
}

export interface JobPost {
  id: string;
  url?: string | null;
  title?: string | null;
  company?: string | null;
  location?: string | null;
  source: string;
  status: string;
  raw_text?: string | null;
  parsed_fields?: JobParsedFields | null;
  created_at: string;
  updated_at: string;
}

export interface JobPostListOut {
  jobs: JobPost[];
  total: number;
}

export interface JobAnalysisReport {
  matched_skills?: string[];
  missing_skills?: string[];
  adjacent_strengths?: string[];
  strengths?: string[];
  weaknesses?: string[];
  experience_fit?: string | null;
  culture_signals?: string[];
  ats_score?: number | null;
  interview_difficulty?: string | null;
  company_summary?: string | null;
  likely_interview_topics?: string[];
  fit_score?: number | null;
  recommendation?: string | null;
  justification?: string | null;
}

export interface JobAnalysis {
  id: string;
  job_id: string;
  profile_id: string;
  status: string;
  report?: JobAnalysisReport | null;
  error?: string | null;
  provider?: string | null;
  model?: string | null;
  prompt_version?: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobAnalysisListOut {
  analyses: JobAnalysis[];
  total: number;
}

export interface JobAnalysisTrace {
  analysis_id: string;
  prompt_text?: string | null;
  evidence_text?: string | null;
  raw_response?: string | null;
}

export interface MasterResume {
  id: string;
  profile_id: string;
  document_id: string;
  status: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface MasterResumeListOut {
  resumes: MasterResume[];
  total: number;
}

export interface ResumeSection {
  name: string;
  items: string[];
}

export interface ResumeContent {
  summary?: string | null;
  sections?: ResumeSection[];
}

export interface ResumeVersion {
  id: string;
  profile_id: string;
  job_id: string;
  master_resume_id: string;
  version_no: number;
  status: string;
  content?: ResumeContent | null;
  content_text?: string | null;
  error?: string | null;
  provider?: string | null;
  model?: string | null;
  prompt_version?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResumeVersionListOut {
  versions: ResumeVersion[];
  total: number;
}

export interface ResumeVersionTrace {
  version_id: string;
  prompt_text?: string | null;
  evidence_text?: string | null;
  raw_response?: string | null;
}

export type TemplateFormat = "html" | "typst" | "latex" | "docx";
export type OutputFormat = "pdf" | "docx";

export interface ResumeTemplate {
  id: string;
  profile_id?: string | null;
  builtin_key?: string | null;
  name: string;
  description?: string | null;
  format: TemplateFormat;
  source_text?: string | null;
  styles_text?: string | null;
  asset_key?: string | null;
  is_default: boolean;
  status: string;
  is_builtin: boolean;
  created_at: string;
  updated_at: string;
}

export interface ResumeTemplateListOut {
  templates: ResumeTemplate[];
  total: number;
}

export interface RenderFormatCapability {
  format: string;
  engine: string;
  output: string;
  available: boolean;
  reason?: string | null;
}

export interface RenderFormatsOut {
  formats: RenderFormatCapability[];
}

export interface RenderJob {
  id: string;
  profile_id: string;
  template_id?: string | null;
  resume_version_id?: string | null;
  output_format: string;
  engine?: string | null;
  status: string;
  filename?: string | null;
  file_size_bytes?: number | null;
  error?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RenderJobListOut {
  jobs: RenderJob[];
  total: number;
}

export interface PdfImportResult {
  content: ResumeContent;
  name?: string | null;
  title?: string | null;
  contact?: string | null;
}
