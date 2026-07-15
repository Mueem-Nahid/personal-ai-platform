"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { api } from "@/lib/api-client";
import type { Profile } from "@/lib/types";

export function useProfiles() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const loaded = useRef(false);

  const loadProfiles = useCallback(async () => {
    if (loaded.current) return;
    try {
      setLoading(true);
      const data = await api.listProfiles();
      setProfiles(data);
      if (data.length > 0) {
        setSelectedProfile(data[0]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load profiles");
    } finally {
      setLoading(false);
      loaded.current = true;
    }
  }, []);

  useEffect(() => {
    loadProfiles();
  }, [loadProfiles]);

  const createProfile = useCallback(async () => {
    try {
      const profile = await api.createProfile({
        full_name: "New User",
        experiences: [],
        projects: [],
        education: [],
        skills: [],
        certificates: [],
        achievements: [],
        publications: [],
        languages: [],
      });
      setProfiles((prev) => [...prev, profile]);
      setSelectedProfile(profile);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create profile");
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);
  const setErrorFn = useCallback((msg: string) => setError(msg), []);

  return {
    profiles,
    selectedProfile,
    setSelectedProfile,
    loading,
    error,
    createProfile,
    clearError,
    setError: setErrorFn,
  };
}
