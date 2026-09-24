import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../common/Button';
import { LogOut } from 'lucide-react';

const SCROLL_THRESHOLD = 24;

const navLinkClass = `
  font-[Inter] text-[13px] font-medium leading-5
  text-[#57534E] transition-colors hover:text-[#1C1917]
`;

export const Navbar: React.FC = () => {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > SCROLL_THRESHOLD);
    onScroll(); // set correct state on mount (e.g. page reloaded mid-scroll)
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    // Fixed-height sticky wrapper: keeps layout stable while the inner bar morphs.
    <header className="pointer-events-none sticky top-0 z-50 h-16 px-0">
      <nav
        className={`
          pointer-events-auto
          mx-auto
          border
          bg-[#FAF7F0]
          transition-all duration-300 ease-out
          ${scrolled
            ? 'mt-3 h-14 max-w-[960px] rounded-full border-[#E8E2D5] bg-[#FAF7F0]/85 shadow-[0_8px_24px_-8px_rgba(28,25,23,0.18)] backdrop-blur-md'
            : 'mt-0 h-16 max-w-full rounded-none border-transparent border-b-[#E8E2D5]'
          }
        `}
      >
        <div
          className={`
            mx-auto h-full w-full transition-all duration-300
            ${scrolled ? 'px-5 sm:px-6' : 'max-w-[1120px] px-4 sm:px-6 lg:px-8'}
          `}
        >
          <div className="flex h-full items-center justify-between">
            {/* ===================== BRAND ===================== */}
            <Link
              to="/"
              className="group flex items-center gap-2"
              aria-label="Legalyze home"
            >
              <img
                src="/logo.svg"
                onError={(e) => {
                  const target = e.currentTarget;
                  if (!target.src.endsWith('/screen.png')) {
                    target.src = '/screen.png';
                  }
                }}
                alt="Legalyze Logo"
                className={`
                  w-auto object-contain transition-all duration-300 group-hover:scale-105
                  ${scrolled ? 'h-7' : 'h-8'}
                `}
              />

              <span
                className="
                  hidden border-l border-[#D0C4BE] pl-2
                  font-[JetBrains_Mono] text-[10px] font-medium uppercase
                  tracking-[0.04em] text-[#8A857C] sm:inline
                "
              >
                Intelligence
              </span>
            </Link>

            {/* ===================== NAVIGATION ===================== */}
            <div className="flex items-center gap-6">
              {!isAuthenticated && (
                <div className="hidden items-center gap-7 md:flex">
                  <a href="/#how-it-works" className={navLinkClass}>
                    Platform Architecture
                  </a>
                  <a href="/#features" className={navLinkClass}>
                    Playbook Auditing
                  </a>
                  {/* <a href="/#benchmarks" className={navLinkClass}>
                    Benchmarks
                  </a> */}
                  <a href="/#faq" className={navLinkClass}>
                    FAQ
                  </a>
                </div>
              )}

              {/* ===================== AUTH ACTIONS ===================== */}
              <div className="flex items-center gap-3">
                {isAuthenticated ? (
                  <>
                    <Link
                      to="/dashboard"
                      className="
                        font-[Inter] text-[13px] font-medium leading-5
                        text-[#1C1917] transition-colors hover:text-[#B08D57]
                      "
                    >
                      Workspace
                    </Link>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleLogout}
                      className="
                        h-9 rounded-full px-3
                        font-[Inter] text-[13px] font-medium text-[#57534E]
                        hover:bg-[#F4EFE6] hover:text-[#1C1917]
                      "
                    >
                      <LogOut className="mr-1.5 h-3.5 w-3.5" />
                      Sign out
                    </Button>
                  </>
                ) : (
                  <>
                    <Link
                      to="/login"
                      className="
                        rounded-full px-2 py-2
                        font-[Inter] text-[13px] font-medium leading-5
                        text-[#1C1917] transition-colors hover:text-[#B08D57]
                      "
                    >
                      Sign in
                    </Link>

                    <Link to="/register">
                      <Button
                        variant="brass"
                        size="sm"
                        className="
                          h-9 rounded-full bg-[#B08D57] px-4
                          font-[Inter] text-[13px] font-medium text-white
                          hover:bg-[#9C7C4B]
                        "
                      >
                        Request Access
                      </Button>
                    </Link>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </nav>
    </header>
  );
};