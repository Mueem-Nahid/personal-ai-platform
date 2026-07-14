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
