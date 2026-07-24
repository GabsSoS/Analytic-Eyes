import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ErrorScreen from "./ErrorScreen";

const REDIRECT_DELAY_MS = 1800;

const ProtectedRoute = ({ children }) => {
  const navigate = useNavigate();
  const token = localStorage.getItem("token");
  const [secondsLeft, setSecondsLeft] = useState(Math.ceil(REDIRECT_DELAY_MS / 1000));

  useEffect(() => {
    if (token) return;

    const redirectTimer = setTimeout(() => {
      navigate("/login", { replace: true });
    }, REDIRECT_DELAY_MS);

    const tickTimer = setInterval(() => {
      setSecondsLeft((s) => Math.max(0, s - 1));
    }, 1000);

    return () => {
      clearTimeout(redirectTimer);
      clearInterval(tickTimer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  if (!token) {
    return (
      <ErrorScreen
        variant="401"
        autoRedirectLabel={`Redirecionando para o login em ${secondsLeft}s...`}
        ctaLabel="Ir para o login agora"
        onCtaClick={() => navigate("/login", { replace: true })}
      />
    );
  }

  return children;
};

export default ProtectedRoute;
