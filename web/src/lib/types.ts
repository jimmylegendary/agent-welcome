export type Platform = 'macos' | 'windows' | 'ios' | 'android' | 'linux' | 'unknown';
export type SupportStatus = 'supported' | 'conditional' | 'unsupported' | 'unverified';
export type CategoryId = 'start' | 'development' | 'data' | 'automation' | 'publish' | 'social' | 'google' | 'creative';
export interface SupportDecision { status: SupportStatus; reason: string }
export interface Source { title: string; url: string; checkedAt: string }
export interface GuideScreenshot { src: string; alt: string; caption: string; sourceUrl: string; capturedAt: string; kind: 'public-page' | 'official-guide' }
export interface SetupAction {
  id: string;
  label: string;
  kind: 'web' | 'download' | 'local-install' | 'local-build' | 'local-browser';
  href?: string;
  command?: string;
  platformCommands?: Partial<Record<Platform, string>>;
  support: Partial<Record<Platform, SupportDecision>>;
}
export interface GuideStep {
  id: string;
  title: string;
  body: string;
  actionId?: string;
  code?: string;
  note?: string;
}
export interface ServiceGuide {
  id: string;
  slug: string;
  name: string;
  subtitle: string;
  description: string;
  category: CategoryId;
  icon: string;
  tags: string[];
  featured?: boolean;
  estimatedMinutes: number;
  billing: string;
  credential: string;
  outcome: string;
  steps: GuideStep[];
  actions: SetupAction[];
  screenshot: GuideScreenshot;
  sources: Source[];
  relatedIds: string[];
}
export interface Category { id: CategoryId; label: string; description: string; icon: string }
export interface StarterPack { id: string; name: string; description: string; icon: string; serviceIds: string[]; firstResult: string }
export interface ModelProfile {
  id: string;
  role: string;
  name: string;
  modelId: string;
  provider: string;
  modality: 'text' | 'image' | 'video' | 'decision';
  description: string;
  endpoint: string;
  pricingNote: string;
  licenseNote: string;
  sourceUrl: string;
  verifiedAt: string;
}
export interface BrowserTool {
  id: string;
  name: string;
  role: string;
  strengths: string;
  limits: string;
  recommendation: string;
  sourceUrl: string;
}
