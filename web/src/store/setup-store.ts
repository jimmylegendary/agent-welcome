'use client';

import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import type { Platform } from '@/lib/types';

type PersistedSetupState = Pick<SetupState, 'platformOverride' | 'completedGuideStepIds'>;

interface SetupState {
  detectedPlatform: Platform;
  platformOverride: Platform | null;
  completedGuideStepIds: string[];
  hasHydrated: boolean;
  setDetectedPlatform: (platform: Platform) => void;
  setPlatformOverride: (platform: Platform | null) => void;
  setGuideStepComplete: (stepId: string, complete: boolean) => void;
  resetGuideSteps: (stepIds: string[]) => void;
  setHasHydrated: (complete: boolean) => void;
  completeHydration: (detectedPlatform: Platform) => void;
}

export const SETUP_STORAGE_KEY = 'agent-welcome-simple-mode';

export const useSetupStore = create<SetupState>()(
  persist(
    (set) => ({
      detectedPlatform: 'unknown',
      platformOverride: null,
      completedGuideStepIds: [],
      hasHydrated: false,
      setDetectedPlatform: (detectedPlatform) => set({ detectedPlatform }),
      setPlatformOverride: (platformOverride) => set({ platformOverride }),
      setGuideStepComplete: (stepId, complete) =>
        set((state) => {
          const completed = new Set(state.completedGuideStepIds);
          if (complete) completed.add(stepId);
          else completed.delete(stepId);
          return { completedGuideStepIds: [...completed] };
        }),
      resetGuideSteps: (stepIds) => {
        const resetIds = new Set(stepIds);
        set((state) => ({
          completedGuideStepIds: state.completedGuideStepIds.filter((id) => !resetIds.has(id)),
        }));
      },
      setHasHydrated: (hasHydrated) => set({ hasHydrated }),
      completeHydration: (detectedPlatform) => set({ detectedPlatform, hasHydrated: true }),
    }),
    {
      name: SETUP_STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
      skipHydration: true,
      partialize: (state) =>
        ({
          platformOverride: state.platformOverride,
          completedGuideStepIds: state.completedGuideStepIds,
        }) satisfies PersistedSetupState,
      onRehydrateStorage: () => (state) => state?.setHasHydrated(true),
    },
  ),
);

export const selectActivePlatform = (state: SetupState): Platform =>
  state.platformOverride ?? state.detectedPlatform;
