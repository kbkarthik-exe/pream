import Link from "next/link";
import {
  ShieldCheck,
  FileText,
  Image as ImageIcon,
  Film,
  BarChart3,
  ArrowRight,
  Download,
  Cpu,
} from "lucide-react";

export default function HomePage() {
  const forensicModalities = [
    {
      title: "Text Forensics",
      code: "MOD-TXT-01",
      icon: FileText,
      desc: "Transformer classification via RoBERTa, Shannon entropy mapping, and lexical burstiness variance.",
      status: "Pipeline Verified",
      badgeColor: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10",
      href: "/dashboard/text",
    },
    {
      title: "Image Authenticity",
      code: "MOD-IMG-02",
      icon: ImageIcon,
      desc: "Swin Vision Transformer, 2D Fast Fourier Transform octant anisotropy, and Laplacian noise residuals.",
      status: "Pipeline Verified",
      badgeColor: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10",
      href: "/dashboard/image",
    },
    {
      title: "Video Deepfakes",
      code: "MOD-VID-03",
      icon: Film,
      desc: "Temporal coherence metrics, facial landmark boundary warping, and frame-rate jitter.",
      status: "Configuration Required",
      badgeColor: "text-amber-400 border-amber-500/30 bg-amber-500/10",
      href: "/dashboard/video",
    },
    {
      title: "Model Benchmarking",
      code: "BENCH-04",
      icon: BarChart3,
      desc: "Empirical confusion matrix, 95% Wilson Score confidence intervals, and Brier score calibration.",
      status: "Operational",
      badgeColor: "text-[#D6B15E] border-[#D6B15E]/30 bg-[#D6B15E]/10",
      href: "/dashboard/evaluation",
    },
  ];

  const platformPillars = [
    {
      title: "Calibrated Decision Boundaries",
      desc: "Every prediction is framed within scientific probabilistic boundaries. Transparently differentiates likely AI generation, human authenticity, and inconclusive results.",
      icon: ShieldCheck,
    },
    {
      title: "Zero-Mock Evidentiary Architecture",
      desc: "Inference metrics and dashboard records are calculated from concrete neural weights and genuine database records. No fabricated figures or simulated results.",
      icon: Cpu,
    },
    {
      title: "Signed Forensic PDF Reports",
      desc: "In-memory two-pass streaming PDF generator produces tamper-evident audit certificates with cryptographic SHA-256 hashes and evidentiary breakdowns.",
      icon: Download,
    },
  ];

  return (
    <main className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8 space-y-24">
      {/* Hero Section */}
      <div className="flex flex-col items-center text-center pt-8">
        <div className="inline-flex items-center gap-2 rounded-full border border-[#D6B15E]/30 bg-[#12151B] px-4 py-1.5 text-xs text-[#F0D58A] shadow-[0_0_15px_rgba(214,177,94,0.1)]">
          <ShieldCheck className="h-4 w-4 text-[#D6B15E]" />
          <span className="font-mono font-bold tracking-wider text-[#D6B15E]">
            SYNTHETIC MEDIA DETECTION
          </span>
          <span className="text-[#3A404D]">&bull;</span>
          <span>Deep Learning Framework</span>
        </div>

        <h1 className="mt-8 text-3xl font-extrabold tracking-tight text-[#F5F5F2] sm:text-5xl lg:text-6xl sm:leading-tight max-w-5xl">
          A Multimodal Deep Learning Framework for{" "}
          <span className="bg-gradient-to-r from-[#D6B15E] via-[#F0D58A] to-[#D6B15E] bg-clip-text text-transparent">
            Robust Detection of Synthetic Media
          </span>
        </h1>

        <p className="mt-5 max-w-3xl text-sm sm:text-base text-[#A3A7B0] leading-relaxed">
          Detect. Analyze. Explain. Verify. High-assurance multimodal deep learning intelligence
          evaluating text, synthesized raster imagery, and temporal video artifacts with calibrated
          uncertainty quantification and forensic provenance.
        </p>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 rounded-xl border border-[#D6B15E]/50 bg-gradient-to-r from-[#D6B15E] to-[#F0D58A] px-6 py-3.5 text-xs font-bold text-[#090A0D] shadow-[0_0_20px_rgba(214,177,94,0.25)] transition-all hover:scale-[1.02] cursor-pointer"
          >
            <span>Launch Forensics Console</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/login"
            className="flex items-center gap-2 rounded-xl border border-[#292D35] bg-[#12151B] px-6 py-3.5 text-xs font-medium text-[#F5F5F2] transition-colors hover:border-[#D6B15E]/60 hover:text-[#D6B15E] cursor-pointer"
          >
            <span>Analyst Portal Access</span>
          </Link>
        </div>
      </div>

      {/* Forensic Modalities Grid */}
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-[#292D35] pb-4 gap-2">
          <div>
            <h2 className="text-base font-bold tracking-wide text-[#F5F5F2] uppercase font-mono">
              Forensic Modality Architecture
            </h2>
            <p className="text-xs text-[#A3A7B0]">
              Decoupled detection layers with genuine neural weights and spatial frequency telemetry
            </p>
          </div>
          <span className="font-mono text-xs text-[#D6B15E]">
            4 ENGINES SPECIFIED
          </span>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {forensicModalities.map((mod) => {
            const Icon = mod.icon;
            return (
              <Link
                key={mod.code}
                href={mod.href}
                className="group relative flex flex-col justify-between rounded-2xl border border-[#292D35] bg-[#12151B] p-6 backdrop-blur-sm transition-all hover:border-[#D6B15E]/50 hover:bg-[#181C23] hover:shadow-[0_0_20px_rgba(214,177,94,0.12)] cursor-pointer"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-[#D6B15E]/40 bg-[#181C23] text-[#D6B15E] group-hover:border-[#D6B15E] transition-colors">
                      <Icon className="h-5 w-5" />
                    </span>
                    <span className={`rounded-full px-2.5 py-0.5 text-[9px] font-mono font-bold border ${mod.badgeColor}`}>
                      {mod.status}
                    </span>
                  </div>

                  <h3 className="mt-5 text-sm font-bold text-[#F5F5F2] group-hover:text-[#F0D58A] transition-colors">
                    {mod.title}
                  </h3>
                  <p className="mt-2 text-xs leading-relaxed text-[#A3A7B0]">
                    {mod.desc}
                  </p>
                </div>

                <div className="mt-6 flex items-center justify-between border-t border-[#292D35] pt-3 text-xs font-mono">
                  <span className="text-[10px] text-[#737984]">{mod.code}</span>
                  <span className="text-[#D6B15E] flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                    <span>Inspect</span>
                    <ArrowRight className="h-3 w-3" />
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Platform Scientific Pillars */}
      <div className="rounded-3xl border border-[#292D35] bg-[#12151B] p-8 sm:p-10 shadow-sm">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <span className="font-mono text-xs text-[#D6B15E] font-bold uppercase tracking-wider">
            Enterprise Standard
          </span>
          <h2 className="mt-2 text-2xl font-bold text-[#F5F5F2] sm:text-3xl">
            High-Assurance Scientific Design
          </h2>
          <p className="mt-2 text-xs text-[#A3A7B0]">
            Engineered to meet the rigor of law enforcement, intelligence analysts, and academic researchers.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {platformPillars.map((pillar, i) => {
            const Icon = pillar.icon;
            return (
              <div
                key={i}
                className="rounded-2xl border border-[#292D35] bg-[#181C23] p-6 space-y-3"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-[#D6B15E]/40 bg-[#12151B] text-[#D6B15E]">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="text-sm font-bold text-[#F5F5F2]">{pillar.title}</h3>
                <p className="text-xs text-[#A3A7B0] leading-relaxed">{pillar.desc}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-[#292D35] pt-8 pb-12 text-center text-xs text-[#737984]">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 font-mono text-[11px]">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-[#D6B15E]" />
            <span className="text-[#F5F5F2]">AICF Forensic Intelligence Platform</span>
            <span>&bull;</span>
            <span>v0.2.0</span>
          </div>

          <div className="text-[#737984]">
            Probabilistic classification telemetry. Corroborate with cryptographic chain-of-custody.
          </div>
        </div>
      </footer>
    </main>
  );
}
