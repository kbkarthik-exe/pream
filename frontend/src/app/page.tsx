import Link from "next/link";

export default function HomePage() {
  const forensicModalities = [
    {
      title: "Text Synthetics",
      code: "MOD-TXT-01",
      desc: "Perplexity gradient mapping, burstiness variance, and semantic hallucination signatures.",
      status: "Pipeline Ready",
    },
    {
      title: "Image Authenticity",
      code: "MOD-IMG-02",
      desc: "Frequency artifact analysis, diffusion noise residuals, and EXIF forensic telemetry.",
      status: "Pipeline Ready",
    },
    {
      title: "Video Deepfakes",
      code: "MOD-VID-03",
      desc: "Temporal coherence metrics, facial landmark boundary warping, and frame-rate jitter.",
      status: "Pipeline Ready",
    },
    {
      title: "Voice & Audio Clones",
      code: "MOD-AUD-04",
      desc: "Spectrogram spectral anomalies, vocoder synthesis traces, and acoustic pitch micro-jitter.",
      status: "Pipeline Ready",
    },
  ];

  return (
    <main className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      {/* Hero Section */}
      <div className="flex flex-col items-center text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-[#D4AF37]/30 bg-[#12141A]/90 px-3.5 py-1 text-xs text-[#F3E5AB] shadow-[0_0_15px_rgba(212,175,55,0.1)]">
          <span className="font-mono font-semibold tracking-wider text-[#D4AF37]">
            AICF 0.1.0 FOUNDATION
          </span>
          <span className="text-[#6B7280]">&bull;</span>
          <span>Forensic Architecture Verified</span>
        </div>

        <h1 className="mt-6 text-4xl font-extrabold tracking-tight text-white sm:text-6xl sm:leading-tight">
          AI Content Forensics &amp;{" "}
          <span className="bg-gradient-to-r from-[#D4AF37] via-[#F3E5AB] to-[#D4AF37] bg-clip-text text-transparent">
            Authenticity Intelligence
          </span>
        </h1>

        <p className="mt-4 max-w-2xl text-base text-[#9FA6B2] sm:text-lg">
          Detect. Analyze. Explain. Verify. Enterprise-grade synthetic media forensics
          across text, imagery, video, and synthetic speech.
        </p>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/login"
            className="flex items-center gap-2 rounded-lg border border-[#D4AF37]/50 bg-gradient-to-r from-[#D4AF37] to-[#F3E5AB] px-6 py-3 text-sm font-semibold text-black shadow-[0_0_20px_rgba(212,175,55,0.25)] transition-all hover:scale-102 hover:shadow-[0_0_30px_rgba(212,175,55,0.4)]"
          >
            Access Forensic Console
            <span aria-hidden="true">&rarr;</span>
          </Link>
          <Link
            href="/dashboard"
            className="rounded-lg border border-[#2B2F3D] bg-[#12141A] px-6 py-3 text-sm font-medium text-[#F8F9FA] transition-colors hover:border-[#D4AF37]/60 hover:text-[#D4AF37]"
          >
            Preview Dashboard Shell
          </Link>
        </div>
      </div>

      {/* Forensic Modalities Grid */}
      <div className="mt-20">
        <div className="flex items-center justify-between border-b border-[#2B2F3D] pb-4">
          <div>
            <h2 className="text-lg font-semibold tracking-wide text-white">
              Forensic Modality Architecture
            </h2>
            <p className="text-xs text-[#9FA6B2]">
              Modular detection layers decoupled from inference runtime
            </p>
          </div>
          <span className="font-mono text-xs text-[#D4AF37]">
            4 DETECTORS SCAFFOLDED
          </span>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {forensicModalities.map((mod) => (
            <div
              key={mod.code}
              className="group relative flex flex-col justify-between rounded-xl border border-[#2B2F3D] bg-[#12141A]/70 p-5 backdrop-blur-sm transition-all hover:border-[#D4AF37]/50 hover:shadow-[0_0_20px_rgba(212,175,55,0.12)]"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[11px] font-semibold text-[#D4AF37]">
                    {mod.code}
                  </span>
                  <span className="rounded-full bg-[#191C24] px-2 py-0.5 text-[10px] text-[#9FA6B2] border border-[#2B2F3D]">
                    {mod.status}
                  </span>
                </div>
                <h3 className="mt-3 text-base font-medium text-white group-hover:text-[#F3E5AB]">
                  {mod.title}
                </h3>
                <p className="mt-2 text-xs leading-relaxed text-[#9FA6B2]">
                  {mod.desc}
                </p>
              </div>

              <div className="mt-6 pt-3 border-t border-[#2B2F3D]/60 flex items-center justify-between text-[11px] text-[#6B7280]">
                <span>Confidence Metric</span>
                <span className="font-mono text-[#D4AF37]">Probabilistic</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Architectural Disclaimers Card */}
      <div className="mt-16 rounded-xl border border-[#2B2F3D] bg-[#12141A]/40 p-6">
        <div className="flex items-start gap-4">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-[#D4AF37]/40 bg-[#191C24] text-xs font-mono text-[#D4AF37]">
            i
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white">
              Scientific &amp; Forensic Transparency Standard
            </h4>
            <p className="mt-1 text-xs leading-relaxed text-[#9FA6B2]">
              AICF adheres to strict forensic reporting standards. Synthetic content detection is fundamentally probabilistic.
              Detection reports highlight likelihood boundaries, feature weights, and confidence intervals rather than claiming absolute binary certainty.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
