export default function Footer() {
  const currentYear = new Date().getFullYear()
  const releaseLabel =
    (typeof window !== 'undefined' && window.__ENV__?.VITE_XSCANNER_RELEASE_TAG) ||
    import.meta.env.VITE_XSCANNER_RELEASE_TAG ||
    __XSCANNER_RELEASE_TAG__ ||
    'dev'

  return (
    <footer className="mt-auto w-full">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="border-t border-gray-400 dark:border-gray-400 pt-8 pb-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-end gap-2">
              <div className="logo-container">
                <img src="/axedras-logo.svg" alt="aXedras Logo" className="h-6 w-auto logo-light" />
                <img src="/axedras-logo-dark.svg" alt="aXedras Logo" className="h-6 w-auto logo-dark" />
              </div>
              <span className="text-sm text-[color:var(--text-secondary)]">© {currentYear} aXedras AG</span>
            </div>

            <div className="flex items-center gap-6 text-sm">
              <span className="text-[color:var(--text-secondary)]">Release: {releaseLabel}</span>
              <a
                href="https://axedras.com"
                target="_blank"
                rel="noopener noreferrer"
                className="transition-colors text-[color:var(--text-secondary)] hover:text-[color:var(--color-gold)]"
              >
                Website
              </a>
              <a
                href="https://www.axedras.com/impressum-privacy-policy"
                target="_blank"
                rel="noopener noreferrer"
                className="transition-colors text-[color:var(--text-secondary)] hover:text-[color:var(--color-gold)]"
              >
                Privacy
              </a>
              <a
                href="https://www.axedras.com/disclaimer"
                target="_blank"
                rel="noopener noreferrer"
                className="transition-colors text-[color:var(--text-secondary)] hover:text-[color:var(--color-gold)]"
              >
                Disclaimer
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}
