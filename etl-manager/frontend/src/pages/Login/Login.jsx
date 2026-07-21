import "./Login.css";
import CartoonImage from "../../assets/Login/rafiki.png";

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../services/api";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!email.trim() || !password.trim()) {
      setError("Por favor, preencha todos os campos");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await api.post("auth/login/", {
        username: email,
        password: password,
      });
      localStorage.setItem("token", res.data.token);
      localStorage.setItem("username", email);
      navigate("/home");
    } catch (err) {
      console.error("Erro no login:", err);
      setError(
        err.response?.data?.error ||
          "Erro ao fazer login. Verifique suas credenciais."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-screen">
      <section className="login-panel">
        <div className="login-panel-inner">
          <div className="login-brand">
            <span className="login-brand-mark" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none">
                <path
                  d="M2 12c2.5-5 6.5-8 10-8s7.5 3 10 8c-2.5 5-6.5 8-10 8s-7.5-3-10-8Z"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinejoin="round"
                />
                <circle cx="12" cy="12" r="3.4" fill="currentColor" />
              </svg>
            </span>
            <span className="login-brand-name">Analytic Eyes</span>
          </div>

          <h1 className="login-title">Bem-vindo de volta</h1>
          <p className="login-subtitle">
            Acesse sua conta para orquestrar, agendar e monitorar seus fluxos
            de dados.
          </p>

          <form className="login-form" onSubmit={handleSubmit}>
            <label className="login-field">
              <span className="login-field-label">Usuário</span>
              <div className="login-input-wrap">
                <svg className="login-input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="8" r="3.6" />
                  <path d="M4.5 20c1.4-3.6 4.4-5.6 7.5-5.6s6.1 2 7.5 5.6" />
                </svg>
                <input
                  id="email"
                  type="text"
                  placeholder="Digite seu nome de usuário"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                  autoComplete="username"
                  required
                />
              </div>
            </label>

            <label className="login-field">
              <span className="login-field-label">Senha</span>
              <div className="login-input-wrap">
                <svg className="login-input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="4.5" y="10.5" width="15" height="9.5" rx="2" />
                  <path d="M8 10.5V7.8a4 4 0 0 1 8 0v2.7" />
                </svg>
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Digite sua senha"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  className="login-toggle-visibility"
                  onClick={() => setShowPassword((v) => !v)}
                  tabIndex={-1}
                  aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                >
                  {showPassword ? (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M3 3l18 18" />
                      <path d="M10.6 10.7a2.5 2.5 0 0 0 3.5 3.5" />
                      <path d="M6.6 6.9C4.5 8.3 2.9 10.3 2 12c1.6 3.4 5.3 7 10 7 1.6 0 3.1-.4 4.4-1.1M12 5c4.7 0 8.4 3.6 10 7-.5 1-1.1 2-1.9 2.9" />
                    </svg>
                  ) : (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M2 12c1.6-3.4 5.3-7 10-7s8.4 3.6 10 7c-1.6 3.4-5.3 7-10 7s-8.4-3.6-10-7Z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
            </label>

            {error && <p className="login-error">{error}</p>}

            <button type="submit" className="login-submit" disabled={loading}>
              {loading ? "Entrando..." : "Entrar"}
            </button>
          </form>
        </div>
      </section>

      <section className="login-showcase">
        <div className="login-showcase-glow" aria-hidden="true" />
        <div className="login-showcase-content">
          <img
            className="login-showcase-image"
            src={CartoonImage}
            alt="Ilustração de fluxo de dados sendo processado"
          />
          <h2>Orquestre seus fluxos ETL com confiança</h2>
          <p>
            Crie pipelines, agende execuções e acompanhe cada etapa em um só
            lugar, com isolamento seguro em containers.
          </p>
        </div>
      </section>
    </div>
  );
}

export default Login;
