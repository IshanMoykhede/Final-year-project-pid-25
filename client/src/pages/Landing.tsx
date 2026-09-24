import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight, PlayCircle, ShieldCheck, Pin, Link as LinkIcon, Paperclip, Search,
  ArrowUp, Gavel, BookOpen, EyeOff, AlertTriangle, CheckCircle2, Shield, Layers,
  Scale, Table, Tag, Lock, ChevronDown, Rocket, Boxes, GraduationCap,
} from 'lucide-react';

/* ------------------------------------------------------------------ */
/* Shared building blocks                                              */
/* ------------------------------------------------------------------ */

const focusRing =
  'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brass';
const btn = `inline-flex items-center justify-center gap-2 rounded-full px-7 py-3.5 text-sm font-medium transition-colors ${focusRing}`;
const card = 'rounded-3xl border border-sand bg-surface shadow-subtle';
const iconBox =
  'mb-5 flex h-10 w-10 items-center justify-center rounded-full border border-sand bg-parchment';

const Eyebrow: React.FC<{ light?: boolean; children: React.ReactNode }> = ({ light, children }) => (
  <p className={`mb-3 font-sans text-sm font-medium ${light ? 'text-brass-soft' : 'text-brass-deep'}`}>
    {children}
  </p>
);

const Container: React.FC<{ id?: string; className?: string; children: React.ReactNode }> = ({
  id, className = '', children,
}) => (
  <section id={id} className={`mx-auto w-full max-w-[1120px] px-4 py-20 sm:px-6 md:py-28 lg:px-8 ${className}`}>
    {children}
  </section>
);

/** Floating rounded band, matching the capsule navbar and footer. */
const Band: React.FC<{
  id?: string;
  tone: 'parchment' | 'dark' | 'surface';
  compact?: boolean;
  children: React.ReactNode;
}> = ({ id, tone, compact, children }) => {
  const tones = {
    parchment: 'bg-parchment border border-sand',
    surface: 'bg-surface border border-sand shadow-card',
    dark: 'bg-charcoal text-ivory',
  };
  return (
    <section id={id} className="px-3 py-3 sm:px-4">
      <div className={`mx-auto max-w-[1200px] rounded-[32px] sm:rounded-[48px] ${tones[tone]}`}>
        <div
          className={`mx-auto max-w-[1120px] px-6 sm:px-10 lg:px-12 ${compact ? 'py-8' : 'py-16 md:py-24'
            }`}
        >
          {children}
        </div>
      </div>
    </section>
  );
};

/* ------------------------------------------------------------------ */
/* Content                                                             */
/* ------------------------------------------------------------------ */

const faqs = [
  {
    q: 'How does Legalyze differ from regular AI chat tools?',
    a: 'General purpose AI tools compress documents into arbitrary token chunks, cutting clauses in half and hallucinating terms when cross-references span multiple pages. Legalyze parses documents along actual statutory and clause boundaries, building a deterministic dependency graph of all cross-references before synthesizing any response.',
  },
  {
    q: 'Does Legalyze use my confidential agreements to train models?',
    a: 'No. Never. We enforce a strict Zero Model Training guarantee. Your contracts, NDAs, and deal memos are processed strictly inside private tenant-isolated containers and are discarded or stored according to your data retention policies.',
  },
  {
    q: 'Can Legalyze handle scanned PDFs and low-resolution documents?',
    a: 'Yes. Our processing engine combines specialized judicial OCR with document structure restoration. It correctly recognizes multi-column layouts, tables of contents, margin notes, and signed annexes.',
  },
  {
    q: 'What file formats and sizes are supported?',
    a: 'We support PDF (both native digital and scanned), DOCX, and TXT files up to 200MB or 400 pages per document. Batch analysis and multi-document comparisons are available for enterprise accounts.',
  },
  {
    q: 'Can Legalyze substitute for my legal counsel?',
    a: 'No. Legalyze is an informational document intelligence and reading tool. It assists attorneys and executives in navigating complex agreements faster and with higher precision, but it does not furnish formal legal counsel or opinions of law.',
  },
];

const docTypes = [
  'Master Services Agreements', 'Commercial Leases', 'Vendor NDAs',
  'Employment Contracts', 'Data Processing Addenda', 'Enterprise SaaS Agreements',
];

const problems = [
  {
    icon: BookOpen, title: 'Long and dense.',
    body: '50+ pages of interlocking terms, sub-clauses, and cross-references designed to withstand litigation, not facilitate quick comprehension.',
    label: 'Average density', value: '48 cross-links / doc',
  },
  {
    icon: EyeOff, title: 'Easy to overlook.',
    body: 'Exceptions, carve-outs, and governing conditions hide far from the clause they change, tucked into definitions schedules or side letters.',
    label: 'Risk vector', value: 'Dormant carve-outs',
  },
  {
    icon: AlertTriangle, title: 'Costly to get wrong.',
    body: 'One missed line can mean unexpected liability, uncapped indemnification, automatic renewals, or forfeiture of critical IP rights.',
    label: 'Financial impact', value: 'Uncapped exposure', danger: true,
  },
];

const steps = [
  { n: '01', title: 'Upload', body: 'Drop in a PDF. We read it reliably, including multi-column scans, headers, footers, and complex table schedules.' },
  { n: '02', title: 'Understand', body: 'Legalyze breaks the document into its real clauses and maps how they relate to one another across sections, annexes, and rider addenda.' },
  { n: '03', title: 'Ask', body: 'Get clear answers, each paired with the exact clauses it came from. Verify citations in one click on the original high-resolution page.' },
];

const pipeline = [
  ['Reading document...', 'Done · Parsed'],
  // ['Reading document...', 'Done · 142ms'],
  ['Identifying clauses...', 'Done · 54 clauses'],
  ['Mapping relationships...', 'Done · 28 links'],
];

const riskBadge = (cls: string, text: string) => (
  <span key={text} className={`rounded-full border px-2.5 py-0.5 font-mono text-[10px] font-medium ${cls}`}>{text}</span>
);

// span = column span on lg (grid is 3 cols) → 2/1, 1/2, 2/1 bento rhythm
const features = [
  { icon: CheckCircle2, span: 'lg:col-span-2', title: 'Answers you can verify.', body: 'Every response cites the exact clauses it draws from. Click a citation and the original page opens with the text highlighted in real time.', foot: <span className="font-mono text-[11px] font-semibold text-brass-deep">Citation link: Clause 8.3</span> },
  { icon: Layers, span: '', title: 'Nothing slips through.', body: 'When one clause depends on another, Legalyze brings both into the answer, so you see the full picture, not half of it.', foot: <span className="font-mono text-[11px] text-muted">Dependency graph activated</span> },
  { icon: Scale, span: '', title: 'Reads like a lawyer.', body: 'Documents are split along real clause boundaries, never cut mid-sentence, so structural and statutory meaning stays intact.', foot: <span className="font-mono text-[11px] text-muted">Clause-boundary parser</span> },
  { icon: Table, span: 'lg:col-span-2', title: 'Instant overview.', body: 'See the parties, governing law, effective dates, key terms, and a navigable structured map of the document before you read a single page.', foot: <span className="font-mono text-[11px] text-muted">Entity &amp; jurisdiction extractor</span> },
  { icon: Shield, span: '', title: 'Risk at a glance.', body: 'Flags one-sided rights, uncapped liability, and unbalanced indemnity with a clear score and suggested counter-proposals.', foot: <div className="flex gap-2">{[riskBadge('bg-olive-soft text-olive border-olive/30', 'Low'), riskBadge('bg-amber-soft text-amber-deep border-amber/30', 'Medium'), riskBadge('bg-crimson-soft text-crimson border-crimson/30', 'High')]}</div> },
  { icon: Tag, span: 'lg:col-span-2', title: 'Organized automatically.', body: 'Clauses are labeled by type (financial, termination, indemnity, and more) so you can jump straight to what matters without keyword hunting.', foot: <span className="font-mono text-[11px] text-muted">34 standard legal taxonomies</span> },
];

const audience = [
  { icon: Gavel, title: 'Legal teams', body: 'First-pass reviews in a fraction of the time. Run redlines, extract non-standard language, and prepare briefs with zero hallucinated answers.', tag: 'Appellate & Corporate' },
  { icon: Rocket, title: 'Founders & Startups', body: "Understand what you're signing without a $500 hour. Surface non-standard investor covenants, lockups, and IP assignment clauses instantly.", tag: 'Financing & Commercial' },
  { icon: Boxes, title: 'Procurement & Ops', body: 'Compare vendor terms quickly and surface discrepancies. Track renewal deadlines, SLA penalties, and data protection commitments.', tag: 'Vendor Risk Analysis' },
  { icon: GraduationCap, title: 'Students & Researchers', body: 'Study real agreements with clarity and structured navigation. Trace judicial interpretation and boilerplate drift across precedents.', tag: 'Jurisprudential Study' },
];

type ClauseId = '14-2' | '18-4' | 'ex-a';

/* ------------------------------------------------------------------ */
/* Page                                                                */
/* ------------------------------------------------------------------ */

export const Landing: React.FC = () => {
  const [activeClause, setActiveClause] = useState<ClauseId>('14-2');
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const xref = (id: ClauseId, label: string) => (
    <button
      type="button"
      onClick={() => setActiveClause(id)}
      className={`font-mono text-brass-soft underline decoration-brass/50 underline-offset-4 hover:text-ivory ${focusRing}`}
    >
      {label}
    </button>
  );

  const clauses: { id: ClauseId; chip: string; title: string; tag: string; body: React.ReactNode }[] = [
    {
      id: '14-2', chip: 'Clause 14.2', title: 'Clause 14.2 — Termination for Convenience', tag: 'Pinpoint target',
      body: (<>“Customer may terminate this Agreement or any applicable Statement of Work, in whole or in part, without cause, upon delivering not less than{' '}
        <span className="font-medium text-brass-soft underline decoration-brass underline-offset-4">thirty (30) consecutive calendar days</span>{' '}
        written notice to Provider. In the event of such termination, Customer's liability shall remain strictly restricted to services rendered and approved up to the effective termination date, subject to the cap in {xref('18-4', 'Clause 18.4')}.”</>),
    },
    {
      id: '18-4', chip: 'Clause 18.4', title: 'Clause 18.4 — Aggregate Liability Ceiling', tag: 'Cross-reference',
      body: (<>“Except with respect to indemnification liabilities outlined in {xref('ex-a', 'Exhibit A')}, neither party's aggregate exposure arising out of or related to this agreement shall exceed total fees paid or payable by Customer in the preceding six (6) month period.”</>),
    },
    {
      id: 'ex-a', chip: 'Exhibit A', title: 'Exhibit A — Indemnification Schedules & IP Carve-Outs', tag: 'Schedule annex',
      body: <>“Provider shall defend, indemnify, and hold harmless Customer against any third-party claims alleging infringement of patents, copyrights, or trade secrets, without regard to limitation caps set forth in Clause 18.”</>,
    },
  ];

  return (
    <div className="flex flex-col bg-ivory font-sans text-charcoal antialiased selection:bg-brass/25">
      {/* ============================ 1. HERO ============================ */}
      <section className="relative w-full overflow-hidden rounded-b-[40px] border-b border-sand/40 sm:rounded-b-[56px]">
        <div className="pointer-events-none absolute inset-0 z-0">
          <img
            src="/Hero.png"
            alt=""
            aria-hidden="true"
            className="h-full w-full object-cover object-center opacity-30 mix-blend-multiply"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-[#FFF8F2]/60 via-[#FFF8F2]/75 to-[#FFF8F2]" />
        </div>

        <div className="relative z-10 mx-auto w-full max-w-[1120px] px-4 pb-20 pt-16 sm:px-6 md:pb-28 md:pt-24 lg:px-8">
          <div className="mx-auto flex max-w-4xl flex-col items-center text-center">
            <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-sand bg-surface/80 px-4 py-1.5 backdrop-blur-sm">
              <span className="h-1.5 w-1.5 rounded-full bg-brass" />
              <span className="font-sans text-[13px] font-medium text-brass-deep">Document intelligence for legal teams</span>
            </div>

            <h1 className="mb-6 font-display text-4xl font-normal tracking-tight text-charcoal sm:text-5xl md:text-[60px] md:leading-[68px]">
              Ask your contract anything.<br className="hidden sm:inline" />
              Get the answer, and the clause behind it.
            </h1>

            <p className="mx-auto mb-9 max-w-2xl text-base font-normal leading-relaxed text-stone-muted sm:text-lg">
              Upload a contract, policy, or agreement and ask questions in plain English. Legalyze reads the entire document, connects related clauses, and answers with exact citations you can verify in one click.
            </p>

            <div className="mb-5 flex w-full flex-col items-center justify-center gap-3 sm:w-auto sm:flex-row sm:gap-4">
              <Link to="/dashboard" className={`${btn} w-full bg-charcoal text-ivory shadow-subtle hover:bg-charcoal-deep sm:w-auto`}>
                <span>Analyze a document</span>
                <ArrowRight className="h-4 w-4 text-brass" />
              </Link>
              <a href="#how-it-works" className={`${btn} w-full border border-sand bg-surface text-charcoal shadow-xs hover:border-brass/40 hover:bg-parchment sm:w-auto`}>
                <PlayCircle className="h-4 w-4 text-stone-muted" />
                <span>See how it works</span>
              </a>
            </div>

            <div className="flex items-center gap-2 font-sans text-xs text-muted">
              <ShieldCheck className="h-4 w-4 text-brass" />
              <span>No credit card required · Your documents stay private</span>
            </div>
          </div>

          {/* Product window */}
          <div className="mt-14 w-full overflow-hidden rounded-3xl border border-sand bg-surface text-left shadow-card md:mt-20">
            <div className="flex h-11 items-center justify-between border-b border-sand bg-parchment px-5">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-sand" />
                <span className="h-2.5 w-2.5 rounded-full bg-sand" />
                <span className="h-2.5 w-2.5 rounded-full bg-sand" />
                <span className="ml-2 truncate font-mono text-xs text-muted">MSA_ApexTechnologies_v3.pdf · 42 clauses indexed</span>
              </div>
              <div className="hidden items-center gap-3 sm:flex">
                <span className="rounded-full border border-olive/30 bg-olive-soft px-2.5 py-0.5 font-mono text-[10px] font-medium text-olive">Verified archive</span>
                <span className="font-mono text-[11px] text-muted">Page 14 of 38</span>
              </div>
            </div>

            <div className="grid min-h-[460px] grid-cols-1 lg:grid-cols-12">
              {/* Left: source */}
              <div className="border-b border-sand bg-parchment/35 p-6 md:p-8 lg:col-span-7 lg:border-b-0 lg:border-r">
                <div className="mb-4 flex items-center justify-between">
                  <span className="font-sans text-sm font-medium text-muted">Source contract</span>
                  <span className="rounded-full border border-sand bg-surface px-2.5 py-0.5 font-mono text-[11px] font-medium text-brass-deep">Active clause</span>
                </div>
                <div className="space-y-4 text-sm leading-relaxed text-stone">
                  <p className="font-mono text-xs tracking-tight text-muted">Clause 14.1 (Term). This Master Services Agreement shall commence on the Effective Date...</p>

                  <div className="rounded-2xl border-l-2 border-brass bg-brass-subtle/40 p-5 text-charcoal">
                    <div className="mb-2 flex items-center justify-between gap-3">
                      <span className="font-sans text-xs font-bold">Clause 14.2 (Termination for Convenience &amp; Breach)</span>
                      <span className="shrink-0 font-mono text-[11px] font-semibold text-brass-deep">Matched source</span>
                    </div>
                    <p className="font-clause text-sm leading-relaxed">
                      Either party may terminate this Agreement without cause upon{' '}
                      <span className="rounded bg-brass/20 px-1 py-0.5 font-medium">thirty (30) days prior written notice</span>
                      , except in cases of material breach where immediate written notice shall take effect under the stipulations set forth in{' '}
                      <span className="font-sans font-medium text-brass-deep underline decoration-brass/40">Clause 11.1</span>{' '}
                      and subject to cross-liability caps in{' '}
                      <span className="font-sans font-medium text-brass-deep underline decoration-brass/40">Exhibit B</span>.
                    </p>
                  </div>

                  <p className="font-mono text-xs tracking-tight text-muted">Clause 14.3 (Effect of Termination). Upon receipt of notice pursuant to Clause 14.2, Supplier shall immediately cease all scheduled work packages...</p>

                  <div className="flex items-center gap-4 pt-2 font-mono text-xs text-muted">
                    <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-brass" /> 3 connected cross-references</span>
                    {/* <span>OCR fidelity: 99.8%</span> */}
                    <span>Vector &amp; Semantic Grounding</span>
                  </div>
                </div>
              </div>

              {/* Right: chat */}
              <div className="flex flex-col justify-between bg-surface p-6 md:p-8 lg:col-span-5">
                <div className="space-y-5">
                  <div className="flex items-center justify-between border-b border-sand pb-3">
                    <span className="font-sans text-sm font-bold">Inquiry &amp; clause trace</span>
                    <span className="flex items-center gap-1.5 font-mono text-[11px] font-medium text-olive">
                      <span className="h-1.5 w-1.5 rounded-full bg-olive" /> Grounded analysis
                    </span>
                  </div>

                  <div className="flex flex-col items-end">
                    <div className="max-w-[90%] rounded-2xl rounded-tr-md border border-sand bg-parchment px-4 py-2.5 shadow-xs">
                      <p className="text-xs font-medium">Can the supplier terminate without notice?</p>
                    </div>
                    <span className="mr-1 mt-1 font-mono text-[10px] text-muted">Counsel · Verified prompt</span>
                  </div>

                  <div className="w-full rounded-2xl rounded-tl-md border border-sand bg-surface p-4 shadow-subtle">
                    <div className="mb-2 flex items-center gap-2">
                      <div className="flex h-5 w-5 items-center justify-center rounded-full bg-charcoal"><Gavel className="h-3 w-3 text-ivory" /></div>
                      <span className="font-sans text-xs font-bold">Legalyze synthesis</span>
                    </div>
                    <p className="font-clause text-xs leading-relaxed">
                      Only in cases of <strong className="font-semibold">material breach</strong>. Clause 14.2 requires{' '}
                      <span className="rounded border border-sand bg-parchment px-1 font-mono">30 days' written notice</span>{' '}
                      in all other cases. Notice remedies are strictly subject to cure provisions.
                    </p>
                    <div className="mt-4 border-t border-sand pt-3">
                      <span className="mb-2 block font-sans text-xs text-muted">Verified sources (click to inspect)</span>
                      <div className="flex flex-wrap gap-2">
                        {[[Pin, 'Clause 14.2'], [LinkIcon, 'Clause 11.1'], [Paperclip, 'Exhibit B']].map(([Icon, label]) => {
                          const I = Icon as typeof Pin;
                          return (
                            <button key={label as string} className={`inline-flex items-center gap-1 rounded-full border border-brass/40 bg-parchment px-2.5 py-1 font-mono text-[11px] text-brass-deep transition-colors hover:bg-brass/10 ${focusRing}`}>
                              <I className="h-3 w-3 text-brass" />
                              <span>{label as string}</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-6 flex items-center gap-2 border-t border-sand pt-4">
                  <div className="flex flex-1 items-center justify-between rounded-full border border-sand bg-parchment px-4 py-2 text-xs text-muted">
                    <span>Ask about liabilities, cure periods, or indemnity...</span>
                    <Search className="h-3.5 w-3.5" />
                  </div>
                  <button aria-label="Send" className={`flex h-9 w-9 items-center justify-center rounded-full bg-charcoal text-ivory transition-colors hover:bg-charcoal-deep ${focusRing}`}>
                    <ArrowUp className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================= 2. TRUST STRIP ========================= */}
      <Band tone="parchment" compact>
        <div className="flex flex-col items-center justify-between gap-6 md:flex-row">
          <p className="max-w-xs text-center text-sm leading-relaxed text-stone-muted md:text-left">
            Built for contracts, NDAs, service agreements, leases, policies, and compliance documents
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2 md:justify-end">
            {docTypes.map((t) => (
              <span key={t} className="rounded-full border border-sand bg-surface px-3.5 py-1.5 font-sans text-xs text-charcoal shadow-xs">{t}</span>
            ))}
          </div>
        </div>
      </Band>

      {/* ========================== 3. PROBLEM ========================== */}
      <Container>
        <div className="mb-14 max-w-2xl">
          <Eyebrow>The structural reality</Eyebrow>
          <h2 className="mb-4 font-display text-3xl font-bold sm:text-4xl">Contracts weren't written to be read quickly.</h2>
          <p className="text-base leading-relaxed text-stone-muted sm:text-lg">
            The answer to a simple question is rarely in one place. A single clause can depend on a definition on page 3, an exception on page 27, and an exhibit at the back. Miss one, and you miss the point.
          </p>
        </div>

        {/* Open columns split by hairlines, so it reads differently from the card grids below */}
        <div className="grid gap-10 md:grid-cols-3 md:gap-0 md:divide-x md:divide-sand">
          {problems.map(({ icon: Icon, title, body, label, value, danger }) => (
            <div key={title} className="flex flex-col justify-between border-t border-sand pt-8 md:border-t-0 md:px-8 md:pt-0 md:first:pl-0 md:last:pr-0">
              <div>
                <div className={iconBox}><Icon className={`h-5 w-5 stroke-[1.5] ${danger ? 'text-crimson' : 'text-charcoal'}`} /></div>
                <h3 className="mb-2 font-sans text-lg font-bold">{title}</h3>
                <p className="text-sm leading-relaxed text-stone-muted">{body}</p>
              </div>
              <div className="mt-8 flex items-center justify-between border-t border-sand pt-4 font-mono text-xs text-muted">
                <span>{label}</span>
                <span className={`font-semibold ${danger ? 'text-crimson' : 'text-charcoal'}`}>{value}</span>
              </div>
            </div>
          ))}
        </div>
      </Container>

      {/* ========================= 4. HOW IT WORKS ========================= */}
      <Band id="how-it-works" tone="parchment">
        <div className="mb-14 flex flex-col justify-between gap-6 md:flex-row md:items-end">
          <div>
            <Eyebrow>Deterministic extraction</Eyebrow>
            <h2 className="font-display text-3xl font-bold sm:text-4xl">From upload to answer in three steps.</h2>
          </div>
          <p className="max-w-md text-sm text-stone-muted">
            Every file is decomposed structurally into clean legal tokens without cutting sentences or dropping footnote cross-references.
          </p>
        </div>

        <div className="grid items-start gap-10 lg:grid-cols-12">
          {/* Sequence → numbered timeline is appropriate here */}
          <ol className="relative space-y-10 before:absolute before:bottom-4 before:left-5 before:top-4 before:w-px before:bg-sand lg:col-span-6">
            {steps.map((s) => (
              <li key={s.n} className="relative pl-16">
                <span className="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-full border border-sand bg-surface font-mono text-xs font-bold shadow-xs">{s.n}</span>
                <h3 className="mb-1 font-sans text-base font-bold">{s.title}</h3>
                <p className="text-sm leading-relaxed text-stone-muted">{s.body}</p>
              </li>
            ))}
          </ol>

          <div id="pipeline" className={`${card} p-6 md:p-8 lg:col-span-6`}>
            <div className="mb-6 flex items-center justify-between border-b border-sand pb-4">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-charcoal" />
                <span className="font-sans text-sm font-bold">Realtime parsing pipeline</span>
              </div>
              <span className="rounded-full border border-sand bg-parchment px-2.5 py-0.5 font-mono text-[10px] text-muted">SSE stream</span>
            </div>

            <div className="space-y-3">
              {pipeline.map(([label, status]) => (
                <div key={label} className="flex items-center justify-between rounded-2xl border border-sand bg-parchment/60 p-3.5">
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-olive" />
                    <span className="font-sans text-xs font-medium">{label}</span>
                  </div>
                  <span className="font-mono text-[11px] font-medium text-olive">{status}</span>
                </div>
              ))}
              <div className="flex items-center justify-between rounded-2xl border border-brass/35 bg-brass-subtle/50 p-3.5">
                <div className="flex items-center gap-3">
                  <span className="relative ml-1 flex h-2.5 w-2.5">
                    <span className="absolute inline-flex h-full w-full rounded-full bg-brass opacity-75 motion-safe:animate-ping" />
                    <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-brass" />
                  </span>
                  <span className="ml-1 font-sans text-xs font-semibold">Ready for analysis</span>
                </div>
                <span className="font-mono text-[11px] font-semibold text-brass-deep">Awaiting query</span>
              </div>
            </div>

            <div className="mt-6 flex items-center justify-between border-t border-sand pt-4 font-mono text-xs text-muted">
              <span>Payload: Structured legal tokens</span>
              {/* <span>Latency: 0.8s</span> */}
              <span>Status: Stream connected</span>
            </div>
          </div>
        </div>
      </Band>

      {/* ========================== 5. FEATURES (BENTO) ========================== */}
      <Container id="features">
        <div className="mx-auto mb-14 max-w-2xl text-center">
          <Eyebrow>Engineered rigor</Eyebrow>
          <h2 className="mb-4 font-display text-3xl font-bold sm:text-4xl">Everything you need to read a contract with confidence.</h2>
          <p className="text-base text-stone-muted">
            A workspace specifically crafted around legal syntax, risk hierarchies, and unyielding source attribution.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
          {features.map(({ icon: Icon, span, title, body, foot }) => (
            <div key={title} className={`${card} flex flex-col justify-between p-7 transition-colors hover:border-brass/40 ${span}`}>
              <div>
                <div className={iconBox}><Icon className="h-4 w-4 text-brass-deep" /></div>
                <h3 className="mb-2 font-sans text-base font-bold">{title}</h3>
                <p className="max-w-md text-sm leading-relaxed text-stone-muted">{body}</p>
              </div>
              <div className="mt-7 border-t border-sand pt-4">{foot}</div>
            </div>
          ))}
        </div>
      </Container>

      {/* ========================== 6. SHOWCASE (DARK) ========================== */}
      <Band tone="dark">
        <div className="mb-12 max-w-3xl">
          <Eyebrow light>Interactive verifiability</Eyebrow>
          <h2 className="mb-4 font-display text-3xl font-bold text-ivory sm:text-4xl">Don't just get an answer. See where it came from.</h2>
          <p className="text-base leading-relaxed text-sand/70">
            Legalyze never asks you to take its word for it. Every statement is tied to the source text, and the source is one click away. Click any citation chip below to trace the clause directly to the document.
          </p>
        </div>

        <div className="overflow-hidden rounded-3xl border border-sand/20 bg-charcoal-deep shadow-2xl">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-sand/15 bg-charcoal px-6 py-4">
            <div className="flex items-center gap-3">
              <span className="font-sans text-xs font-medium text-brass-soft">Document inspector</span>
              <span className="text-xs text-sand/40">/</span>
              <span className="font-mono text-xs text-ivory">Apex_Global_Logistics_Services.pdf</span>
            </div>
            <div className="flex items-center gap-2" role="tablist" aria-label="Citations">
              {clauses.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  role="tab"
                  aria-selected={activeClause === c.id}
                  onClick={() => setActiveClause(c.id)}
                  className={`rounded-full px-3.5 py-1.5 font-mono text-xs font-semibold transition-colors ${focusRing} ${activeClause === c.id
                      ? 'bg-brass text-ivory'
                      : 'border border-sand/30 bg-charcoal text-sand hover:border-brass'
                    }`}
                >
                  {c.chip}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-4 bg-[#181D24] p-5 md:p-8">
            {clauses.map((c) => {
              const on = activeClause === c.id;
              return (
                <div
                  key={c.id}
                  className={`rounded-2xl border p-5 transition-all duration-300 ${on ? 'border-brass bg-brass/15 ring-1 ring-brass/40' : 'border-sand/15 bg-charcoal/50'
                    }`}
                >
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <span className={`font-sans text-sm font-bold ${on ? 'text-brass-soft' : 'text-sand/80'}`}>{c.title}</span>
                    <span className={`shrink-0 rounded-full border px-2.5 py-0.5 font-mono text-[11px] ${on ? 'border-brass/30 bg-charcoal text-brass-soft' : 'border-transparent text-sand/60'}`}>{c.tag}</span>
                  </div>
                  <p className={`font-clause text-sm leading-relaxed md:text-base ${on ? 'text-ivory' : 'text-sand/60'}`}>{c.body}</p>
                </div>
              );
            })}
          </div>
        </div>
      </Band>

      {/* ========================== 7. BENCHMARK (COMMENTED OUT: UNPROVABLE CLAIMS) ========================== */}
      {/*
      <Container id="cuad-benchmark">
        <div className="mb-12 max-w-2xl">
          <Eyebrow>Empirical proof</Eyebrow>
          <h2 className="mb-4 font-display text-3xl font-bold sm:text-4xl">Tested on real contracts.</h2>
          <p className="text-base text-stone-muted sm:text-lg">
            In our benchmark on the CUAD legal contract dataset, Legalyze recovered every related clause that a standard AI search missed, roughly 1 in 4 in our tests.
          </p>
        </div>

        <div className="grid gap-5 md:grid-cols-2">
          <div className="rounded-3xl border border-sand bg-parchment p-8">
            <span className="mb-4 block font-sans text-sm font-medium text-muted">Standard AI vector search</span>
            <div className="mb-2 font-display text-[44px] font-normal leading-tight text-crimson">Missed 25.7%</div>
            <p className="text-sm leading-relaxed text-stone-muted">
              Missed 25.7% of related clauses when cross-references were separated by more than 10 pages or referenced in appendix sections.
            </p>
            <div className="mt-8">
              <div className="mb-2 flex justify-between font-mono text-xs text-muted"><span>Related clauses found</span><span className="font-medium text-crimson">74.3%</span></div>
              <div className="h-2 rounded-full bg-sand/70"><div className="h-full rounded-full bg-crimson/70" style={{ width: '74.3%' }} /></div>
            </div>
          </div>

          <div className="rounded-3xl border-2 border-charcoal bg-surface p-8 shadow-card">
            <span className="mb-4 block font-sans text-sm font-medium text-brass-deep">Legalyze structural graph</span>
            <div className="mb-2 font-display text-[44px] font-normal leading-tight">Missed none</div>
            <p className="text-sm leading-relaxed text-stone-muted">
              Missed none in our benchmark across all interconnected clause clusters, cross-liability riders, and governing law schedules.
            </p>
            <div className="mt-8">
              <div className="mb-2 flex justify-between font-mono text-xs text-muted"><span>Related clauses found</span><span className="font-semibold text-olive">100%</span></div>
              <div className="h-2 rounded-full bg-sand/70"><div className="h-full w-full rounded-full bg-olive" /></div>
            </div>
          </div>
        </div>

        <p className="mt-5 font-mono text-xs text-muted">
          * Tested across 510 commercial contracts evaluated on CUAD (Contract Understanding Atticus Dataset) benchmarks.
        </p>
      </Container>
      */}

      {/* ========================== 8. AUDIENCE ========================== */}
      <Band tone="parchment">
        <div className="mb-12 max-w-2xl">
          <Eyebrow>Who it's for</Eyebrow>
          <h2 className="mb-4 font-display text-3xl font-bold sm:text-4xl">Made for people who can't afford to miss things.</h2>
          <p className="text-base text-stone-muted">
            From high-velocity deal desks to boutique practices, clarity on contractual obligations is non-negotiable.
          </p>
        </div>

        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
          {audience.map(({ icon: Icon, title, body, tag }) => (
            <div key={title} className={`${card} flex flex-col justify-between p-6`}>
              <div>
                <div className={iconBox}><Icon className="h-4 w-4 stroke-[1.5]" /></div>
                <h3 className="mb-2 font-sans text-base font-bold">{title}</h3>
                <p className="text-sm leading-relaxed text-stone-muted">{body}</p>
              </div>
              <div className="mt-6 border-t border-sand pt-3 font-mono text-[11px] text-muted">{tag}</div>
            </div>
          ))}
        </div>
      </Band>

      {/* ========================== 9. SECURITY ========================== */}
      <Band id="security" tone="surface">
        <div className="flex flex-col items-start justify-between gap-10 md:flex-row md:items-center">
          <div className="max-w-xl">
            <Eyebrow>Institutional privacy</Eyebrow>
            <h2 className="mb-4 font-display text-3xl font-bold sm:text-4xl">Your documents are yours.</h2>
            <p className="mb-6 text-sm leading-relaxed text-stone-muted">
              Each account is isolated, and files are accessible only to you. We don't sell your data and never use your agreements to train models. Storage is encrypted with AES-256 at rest and TLS 1.3 in transit.
            </p>
            <div className="inline-flex items-center gap-2 rounded-full border border-sand bg-parchment px-4 py-2">
              <ShieldCheck className="h-3.5 w-3.5 text-brass" />
              <span className="font-sans text-xs text-muted">Legalyze is an analysis tool and does not provide legal advice.</span>
            </div>
          </div>

          <div className="flex w-full flex-col gap-3 md:w-auto">
            {[[Lock, 'Zero training policy'], [ShieldCheck, 'SOC 2 Type II compliant infra'], [Lock, 'Tenant-isolated key enclaves']].map(([Icon, label]) => {
              const I = Icon as typeof Lock;
              return (
                <div key={label as string} className="flex items-center gap-3 rounded-full border border-sand bg-parchment px-5 py-3 font-sans text-sm">
                  <I className="h-4 w-4 text-olive" />
                  <span>{label as string}</span>
                </div>
              );
            })}
          </div>
        </div>
      </Band>

      {/* ========================== 10. FAQ ========================== */}
      <section id="faq" className="mx-auto w-full max-w-[800px] px-4 py-20 sm:px-6 md:py-28 lg:px-8">
        <div className="mb-12 text-center">
          <Eyebrow>Clarity &amp; architecture</Eyebrow>
          <h2 className="font-display text-3xl font-bold sm:text-4xl">Frequently asked questions</h2>
        </div>

        <div className="space-y-3">
          {faqs.map((faq, i) => {
            const open = openFaq === i;
            return (
              <div key={faq.q} className={`overflow-hidden rounded-2xl border bg-surface shadow-xs transition-colors ${open ? 'border-brass/40' : 'border-sand'}`}>
                <button
                  type="button"
                  aria-expanded={open}
                  aria-controls={`faq-${i}`}
                  onClick={() => setOpenFaq(open ? null : i)}
                  className={`flex w-full items-center justify-between gap-4 p-5 text-left transition-colors hover:bg-parchment/60 ${focusRing}`}
                >
                  <span className="font-sans text-sm font-bold">{faq.q}</span>
                  <ChevronDown className={`h-4 w-4 shrink-0 transition-transform duration-200 ${open ? 'rotate-180 text-brass' : 'text-muted'}`} />
                </button>
                <div id={`faq-${i}`} className={`grid transition-all duration-300 ${open ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'}`}>
                  <div className="overflow-hidden">
                    <p className="border-t border-sand/40 px-5 pb-5 pt-4 text-sm leading-relaxed text-stone-muted">{faq.a}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ========================== 11. FINAL CTA ========================== */}
      <section className="px-3 pb-3 sm:px-4">
        <div className="relative mx-auto max-w-[1200px] overflow-hidden rounded-[32px] bg-charcoal px-6 py-20 text-center text-ivory sm:rounded-[48px] md:py-28">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(201,164,108,0.22),_transparent_65%)]"
          />
          <div className="relative mx-auto flex max-w-2xl flex-col items-center">
            <h2 className="mb-4 font-display text-4xl font-normal sm:text-5xl md:text-[60px] md:leading-[68px]">Read less. Know more.</h2>
            <p className="mb-9 max-w-lg text-base text-sand/80 sm:text-lg">
              Upload your first document and ask it anything. Get full clause grounding in seconds.
            </p>
            <Link to="/register" className={`${btn} mb-4 bg-ivory px-9 py-4 font-bold text-charcoal shadow-subtle hover:bg-white`}>
              <span>Get started free</span>
              <ArrowRight className="h-4 w-4 text-brass" />
            </Link>
            <span className="text-xs text-sand/60">No credit card required · Instant document review</span>
          </div>
        </div>
      </section>
    </div>
  );
};