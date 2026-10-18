import Link from 'next/link';
import {
  Activity,
  ArrowUpRight,
  AtSign,
  AudioLines,
  BookOpen,
  Bot,
  Boxes,
  Braces,
  Clapperboard,
  Cloud,
  Code2,
  CodeXml,
  Compass,
  Database,
  Film,
  Flame,
  FileCode2,
  Gamepad2,
  Globe2,
  HardDrive,
  Hexagon,
  Image,
  KeyRound,
  Library,
  Layers3,
  Mail,
  Map,
  MonitorCog,
  MousePointerClick,
  Palette,
  Play,
  Presentation,
  Puzzle,
  Rocket,
  Route,
  ScanSearch,
  Share2,
  Smartphone,
  ShieldCheck,
  Table2,
  Sparkles,
  Terminal,
  Triangle,
  Video,
  Workflow,
  type LucideIcon,
} from 'lucide-react';
import type { ServiceGuide } from '@/lib/types';
import { CategoryPill } from '@/components/ui';

const icons: Record<string, LucideIcon> = {
  activity: Activity,
  apple: Smartphone,
  'at-sign': AtSign,
  'audio-lines': AudioLines,
  book: BookOpen,
  bot: Bot,
  boxes: Boxes,
  braces: Braces,
  browser: MousePointerClick,
  clapperboard: Clapperboard,
  cloud: Cloud,
  code: Code2,
  'code-2': Code2,
  'code-xml': CodeXml,
  compass: Compass,
  database: Database,
  film: Film,
  flame: Flame,
  file: FileCode2,
  'gamepad-2': Gamepad2,
  github: Code2,
  globe: Globe2,
  'hard-drive': HardDrive,
  hexagon: Hexagon,
  image: Image,
  instagram: Image,
  'key-round': KeyRound,
  layers: Layers3,
  'layers-3': Layers3,
  library: Library,
  mail: Mail,
  map: Map,
  monitor: MonitorCog,
  'mouse-pointer-click': MousePointerClick,
  palette: Palette,
  play: Play,
  presentation: Presentation,
  puzzle: Puzzle,
  rocket: Rocket,
  route: Route,
  'scan-search': ScanSearch,
  'share-2': Share2,
  sheet: Table2,
  smartphone: Smartphone,
  shield: ShieldCheck,
  sparkles: Sparkles,
  'table-2': Table2,
  terminal: Terminal,
  triangle: Triangle,
  video: Video,
  workflow: Workflow,
  youtube: Play,
};

const categoryTone: Record<string, string> = {
  start: 'tone-emerald',
  development: 'tone-blue',
  data: 'tone-sky',
  automation: 'tone-amber',
  publish: 'tone-rose',
  social: 'tone-blue',
  google: 'tone-blue',
  creative: 'tone-amber',
};

export function ServiceCard({
  service,
  categoryLabel,
  compact = false,
}: {
  service: ServiceGuide;
  categoryLabel: string;
  compact?: boolean;
}) {
  const Icon = icons[service.icon.toLowerCase()] ?? Bot;
  const tone = categoryTone[service.category] ?? 'tone-emerald';

  return (
    <Link
      className={`service-card${compact ? ' service-card-compact' : ''}`}
      href={`/guides/${service.slug}`}
      aria-label={`${service.name} 가이드 열기`}
    >
      <div className="service-card-topline">
        <span className={`service-icon ${tone}`} aria-hidden="true">
          <Icon size={20} strokeWidth={1.8} />
        </span>
        <CategoryPill label={categoryLabel} />
        {service.featured && <span className="featured-label">추천</span>}
      </div>
      <div className="service-card-copy">
        <h3>{service.name}</h3>
        <p className="service-subtitle">{service.subtitle}</p>
        {!compact && <p className="service-description">{service.description}</p>}
      </div>
      <div className="service-card-footer">
        <span>{service.estimatedMinutes}분 안내</span>
        <span className="service-arrow" aria-hidden="true"><ArrowUpRight size={15} /></span>
      </div>
    </Link>
  );
}
