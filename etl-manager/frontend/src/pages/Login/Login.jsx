import "./Login.css";
import OndaEsquerda from '../../assets/Login/onda-esquerda.png';
import OndaDireita from '../../assets/Login/onda-direita.png';
import CartoonImage from '../../assets/Login/rafiki.png';
import Logo from '../../assets/Login/Logo1.png';
import User from '../../assets/Login/user 1.png';
import PasswordIcon from '../../assets/Login/eye-scanner 1.png';

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../services/api";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validação
    if (!email.trim() || !password.trim()) {
      setError("Por favor, preencha todos os campos");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await api.post('auth/login/', {
        username: email,
        password: password
      });
      console.log("Login bem-sucedido:", res.data);
      // Salva o token
      localStorage.setItem('token', res.data.token);
      localStorage.setItem('username', email);
      // Redireciona para home
      navigate('/home');
    } catch (err) {
      console.error("Erro no login:", err);
      setError(err.response?.data?.error || "Erro ao fazer login. Verifique suas credenciais.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="background">
      <div className="onda-esquerda">
        <img src={OndaEsquerda} alt="Onda decorativa esquerda" />
      </div>

      <section className="campo-login">
        <img src={Logo} alt="Logo da empresa" className="logo" />

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="email-input-container">
            <img src={User} alt="Ícone de usuário" className="user-icon" />
            <input
              id="email" 
              className="email" 
              type="text" 
              placeholder="Digite seu nome de usuário" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              required 
            />
          </div>
          <div className="password-input-container">
            <img src={PasswordIcon} alt="Ícone de senha" className="password-icon" />
            <input 
              id="password"
              className="password" 
              type="password" 
              placeholder="Digite sua senha" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              required 
            />
          </div>

          {error && <p className="error-message">{error}</p>}

          <button 
            type="submit" 
            className="login-button"
            disabled={loading}
          >
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>
      </section>

      <img className="foto-walpaper" src={CartoonImage} alt="Imagem ilustrativa" />

      <div className="onda-direita">
        <img src={OndaDireita} alt="Onda decorativa direita" />
      </div>
    </div>
  );
}

export default Login
