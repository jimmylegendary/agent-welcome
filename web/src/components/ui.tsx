import Link from 'next/link';
import { ArrowLeft, ArrowRight, ArrowUpRight, Info } from 'lucide-react';

export function PageHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: { href: string; label: string; back?: boolean };
}) {
  return (
    <div className="page-heading">
      <div className="page-heading-copy">
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {description && <p className="page-description">{description}</p>}
      </div>
      {action && (
        <Link className="button button-secondary page-heading-action" href={action.href}>
          {action.back ? <ArrowLeft size={16} aria-hidden="true" /> : null}
          <span>{action.label}</span>
          {!action.back ? <ArrowRight size={16} aria-hidden="true" /> : null}
        </Link>
      )}
    </div>
  );
}

export function SectionTitle({
  title,
  detail,
  action,
  id,
}: {
  title: string;
  detail?: string;
  action?: { href: string; label: string };
  id?: string;
}) {
  return (
    <div className="section-title-row">
      <div>
        <h2 id={id}>{title}</h2>
        {detail && <p>{detail}</p>}
      </div>
      {action && (
        <Link className="text-link" href={action.href}>
          {action.label} <ArrowUpRight size={15} aria-hidden="true" />
        </Link>
      )}
    </div>
  );
}

export function CategoryPill({ label }: { label: string }) {
  return <span className="category-pill">{label}</span>;
}

export function Note({ children, tone = 'neutral' }: { children: React.ReactNode; tone?: 'neutral' | 'amber' }) {
  return (
    <aside className={`note note-${tone}`}>
      <Info size={17} strokeWidth={1.9} aria-hidden="true" />
      <div>{children}</div>
    </aside>
  );
}

export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="empty-state">
      <span className="empty-state-orbit" aria-hidden="true">
        <Info size={20} />
      </span>
      <h2>{title}</h2>
      <p>{detail}</p>
    </div>
  );
}

export function ExternalSource({ href, label }: { href: string; label: string }) {
  return (
    <a className="source-link" href={href} target="_blank" rel="noopener noreferrer">
      {label} <ArrowUpRight size={14} aria-hidden="true" />
    </a>
  );
}
