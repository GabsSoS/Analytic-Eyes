import "./ErrorScreen.css";

// Tela de erro reutilizável - "404" (rota inexistente) ou "401" (não
// autenticado / sem permissão). Usada em App.jsx (catch-all de rota) e em
// ProtectedRoute.jsx (quando não há token válido).
function ErrorScreen({ variant = "404", ctaLabel, ctaTo, onCtaClick, autoRedirectLabel }) {
  const isAuth = variant === "401";

  return (
    <div className="error-screen">
      <div className="error-screen-card">
        <div className="error-screen-icon" aria-hidden="true">
          {isAuth ? (
            <svg viewBox="0 0 64 64" className="error-screen-svg error-screen-svg-lock">
              <rect x="16" y="28" width="32" height="26" rx="5" className="lock-body" />
              <path
                d="M22 28v-8a10 10 0 0 1 20 0v8"
                className="lock-shackle"
                fill="none"
                strokeWidth="4.5"
                strokeLinecap="round"
              />
              <circle cx="32" cy="39" r="3.4" className="lock-hole" />
              <rect x="30.4" y="41" width="3.2" height="7" rx="1.6" className="lock-hole" />
            </svg>
          ) : (
            <svg viewBox="0 0 64 64" className="error-screen-svg error-screen-svg-search">
              <circle cx="27" cy="27" r="16" className="search-ring" fill="none" strokeWidth="5" />
              <line x1="38.5" y1="38.5" x2="52" y2="52" className="search-handle" strokeWidth="5.5" strokeLinecap="round" />
              <path d="M20 27h14M27 20v14" className="search-plus" strokeWidth="3.5" strokeLinecap="round" />
            </svg>
          )}
          <span className="error-screen-code">{isAuth ? "401" : "404"}</span>
        </div>

        <h1 className="error-screen-title">
          {isAuth ? "Você não tem permissão para acessar esta página" : "Página não encontrada"}
        </h1>
        <p className="error-screen-message">
          {isAuth
            ? "Sua sessão expirou ou você não está autenticado. Faça login novamente para continuar."
            : "O endereço que você tentou acessar não existe ou foi movido."}
        </p>

        {autoRedirectLabel && <p className="error-screen-hint">{autoRedirectLabel}</p>}

        {ctaLabel && (
          ctaTo ? (
            <a href={ctaTo} className="error-screen-btn">{ctaLabel}</a>
          ) : (
            <button type="button" className="error-screen-btn" onClick={onCtaClick}>{ctaLabel}</button>
          )
        )}
      </div>
    </div>
  );
}

export default ErrorScreen;
