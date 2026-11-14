import Link from 'next/link';
import { ArrowRight, ShieldCheck, ScanLine, Gauge, Sparkles } from 'lucide-react';

const features = [
  {
    icon: ScanLine,
    title: 'Preliminary plan review',
    description: 'Produce candidate room and element detections for a reviewer to verify against the source drawing.',
  },
  {
    icon: Gauge,
    title: 'Review checklist',
    description: 'Track what still needs measured, source-backed review. The prototype does not certify code compliance.',
  },
  {
    icon: Sparkles,
    title: 'Decision support',
    description: 'Turn raw architectural data into actionable design recommendations for architects and reviewers.',
  },
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6 lg:px-10">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-cyan-500/15 p-2 text-cyan-300">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <p className="text-lg font-semibold">BuildGuard AI</p>
          </div>
        </div>

        <nav className="hidden items-center gap-6 text-sm text-slate-300 md:flex">
          <Link href="#features" className="transition hover:text-white">Features</Link>
          <Link href="#workflow" className="transition hover:text-white">Workflow</Link>
          <Link href="#about" className="transition hover:text-white">About</Link>
        </nav>

        <div className="flex items-center gap-3">
          <Link href="/login" className="rounded-full border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200 transition hover:border-slate-500 hover:text-white">
            Sign in
          </Link>
          <Link href="/register" className="rounded-full bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400">
            Get started
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 pb-20 pt-10 lg:px-10">
        <section className="grid items-center gap-12 lg:grid-cols-[1.2fr_0.8fr]">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-medium uppercase tracking-[0.2em] text-cyan-300">
              Preliminary plan screening
            </span>
            <h1 className="mt-6 max-w-xl text-5xl font-black tracking-tight text-white lg:text-6xl">
              Model-assisted floor-plan review.
            </h1>
            <p className="mt-6 max-w-xl text-lg text-slate-300">
              BuildGuard AI produces preliminary geometry detections to help organize a plan review. It does not determine NBC compliance or grant approval; a qualified professional must verify the drawing, measurements, applicable rules, and authority.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Link href="/register" className="inline-flex items-center gap-2 rounded-full bg-cyan-500 px-6 py-3 font-semibold text-slate-950 transition hover:bg-cyan-400">
                Start free demo
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link href="/login" className="rounded-full border border-slate-700 px-6 py-3 font-semibold text-white transition hover:border-slate-500 hover:bg-slate-900">
                View dashboard
              </Link>
            </div>

          </div>

          <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 shadow-2xl shadow-cyan-950/20">
            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <p className="text-sm text-slate-400">Current review</p>
                  <p className="text-xl font-semibold text-white">Illustrative detections</p>
                </div>
                <div className="rounded-full bg-amber-500/15 px-2.5 py-1 text-xs font-semibold text-amber-200">
                  NOT ASSESSED
                </div>
              </div>

              <div className="mt-6 space-y-5">
                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-xl bg-slate-900 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Model output</p>
                    <p className="mt-2 text-lg font-bold text-white">Candidate geometry</p>
                  </div>
                  <div className="rounded-xl bg-slate-900 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Code assessment</p>
                    <p className="mt-2 text-lg font-bold text-white">Not assessed</p>
                  </div>
                </div>

                <div className="rounded-xl bg-slate-900 p-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-slate-300">Review status</p>
                    <p className="text-sm font-semibold text-cyan-300">Professional verification required</p>
                  </div>
                  <div className="mt-3 h-2.5 rounded-full bg-slate-800">
                    <div className="h-2.5 w-full rounded-full bg-slate-700" />
                  </div>
                </div>

                <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 text-sm text-amber-100">
                  Example UI only. Detections and dimensions must be verified against the source drawing and applicable rules.
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="mt-28">
          <div className="mb-10 max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">Features</p>
            <h2 className="mt-3 text-3xl font-bold text-white">A prototype for organizing preliminary plan review.</h2>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {features.map(({ icon: Icon, title, description }) => (
              <div key={title} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
                <div className="mb-4 inline-flex rounded-xl bg-cyan-500/10 p-3 text-cyan-300">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="text-xl font-semibold text-white">{title}</h3>
                <p className="mt-3 text-slate-300">{description}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="workflow" className="mt-28 grid gap-6 rounded-3xl border border-slate-800 bg-slate-900/60 p-8 md:grid-cols-4">
          {['Upload plan', 'Detect elements', 'Run rules', 'Review report'].map((step, index) => (
            <div key={step} className="rounded-2xl bg-slate-950/70 p-5">
              <div className="mb-3 inline-flex h-8 w-8 items-center justify-center rounded-full bg-cyan-500/15 text-sm font-semibold text-cyan-300">
                {index + 1}
              </div>
              <p className="text-lg font-semibold text-white">{step}</p>
            </div>
          ))}
        </section>

        <section id="about" className="mt-28 max-w-3xl">
          <div className="rounded-3xl border border-slate-800 bg-gradient-to-r from-slate-900 to-slate-800 p-8">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">About</p>
            <h2 className="mt-3 text-3xl font-bold text-white">Academic prototype for AI-assisted architectural review.</h2>
            <p className="mt-4 text-slate-300">
              Created as a research and prototype platform, BuildGuard AI evaluates building layouts against predefined safety and accessibility principles, helping professionals identify risks earlier in the design process.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}
