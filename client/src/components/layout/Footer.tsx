import React from 'react';
import { Link } from 'react-router-dom';

const linkClass = `
  font-[Inter] text-[13px] leading-5
  text-[#8A857C] transition-colors hover:text-[#FAF7F0]
`;

const mutedClass = 'font-[Inter] text-[13px] leading-5 text-[#57534E]';

const headingClass = `
  font-[JetBrains_Mono] text-[11px] font-medium uppercase
  tracking-[0.04em] text-[#C9A46C]
`;

export const Footer: React.FC = () => (
  // Outer wrapper leaves a cream gutter so the dark footer reads as a floating capsule
  <footer className="bg-[#FAF7F0] px-3 pb-3 pt-6 sm:px-4 sm:pb-4">
    <div
      className="
        mx-auto max-w-[1200px]
        rounded-[32px] sm:rounded-[48px]
        bg-[#1C1917] text-[#FAF7F0]
        shadow-[0_20px_40px_-20px_rgba(28,25,23,0.45)]
      "
    >
      <div className="mx-auto max-w-[1120px] px-6 py-12 sm:px-10 lg:px-12">
        <div className="grid gap-10 md:grid-cols-4">
          {/* ===================== BRAND ===================== */}
          <div className="md:col-span-1">
            <Link
              to="/"
              className="
                inline-flex items-baseline
                font-[Playfair_Display] text-[24px] font-normal
                leading-none tracking-[-0.02em] text-[#FAF7F0]
              "
            >
              LEGALYZE
              <span className="ml-1.5 inline-block h-1.5 w-1.5 rounded-full bg-[#C9A46C]" />
            </Link>

            <p className="mt-4 max-w-xs font-[Inter] text-[13px] leading-5 text-[#8A857C]">
              Grounded contract intelligence and playbook variance
              benchmarking engineered for corporate legal counsel.
            </p>
          </div>

          {/* ===================== PLATFORM ===================== */}
          <div>
            <p className={headingClass}>Platform</p>
            <ul className="mt-4 space-y-2.5">
              <li>
                <a href="/#how-it-works" className={linkClass}>
                  Architecture & RAG
                </a>
              </li>
              <li>
                <a href="/#features" className={linkClass}>
                  Clause Variance Engine
                </a>
              </li>
              {/* <li>
                <a href="/#benchmarks" className={linkClass}>
                  CUAD Benchmark Validation
                </a>
              </li> */}
              <li>
                <Link to="/dashboard" className={linkClass}>
                  Review Console
                </Link>
              </li>
            </ul>
          </div>

          {/* ===================== SPECIFICATIONS ===================== */}
          <div>
            <p className={headingClass}>Specifications</p>
            <ul className="mt-4 space-y-2.5">
              <li>
                <a href="/#faq" className={linkClass}>
                  FAQ & Security Model
                </a>
              </li>
              <li>
                <span className={mutedClass}>Enterprise Playbook Config</span>
              </li>
              <li>
                <span className={mutedClass}>Export API & Audit Trail</span>
              </li>
              <li>
                <span className={mutedClass}>Zero-Retention Policy</span>
              </li>
            </ul>
          </div>

          {/* ===================== REGULATORY & ETHICS ===================== */}
          <div>
            <p className={headingClass}>Regulatory & Ethics</p>
            <ul className="mt-4 space-y-2.5">
              <li>
                <span className={mutedClass}>Strict Citation Grounding</span>
              </li>
              <li>
                <span className={mutedClass}>Privacy & Data Isolation</span>
              </li>
              <li>
                <span className={mutedClass}>Terms of Service</span>
              </li>
            </ul>
          </div>
        </div>

        {/* ===================== BOTTOM DIVIDER ===================== */}
        <div
          className="
            mt-12 flex flex-col items-center justify-between gap-4
            border-t border-[rgba(232,226,213,0.15)] pt-8 sm:flex-row
          "
        >
          <div className="font-[Inter] text-[12px] leading-4 text-[#8A857C]">
            © {new Date().getFullYear()} Legalyze Technologies. All rights reserved.
          </div>

          <div
            className="
              text-center font-[Playfair_Display] text-[13px] italic
              leading-5 text-[#C9A46C] sm:text-right
            "
          >
            "Legalyze is an analytical instrument for legal counsel,
            not an automated attorney."
          </div>
        </div>
      </div>
    </div>
  </footer>
);