import "./Settings.css";
import { useState, useEffect } from "react";
import api from "../../services/api";

function Settings() {
  const [usuarioAtual] = useState(localStorage.getItem("username") || "Usuário");
  const [isStaff, setIsStaff] = useState(false);
  const [loadingUserInfo, setLoadingUserInfo] = useState(true);
  const [loadingPassword, setLoadingPassword] = useState(false);
  const [loadingUser, setLoadingUser] = useState(false);
  const [messagePassword, setMessagePassword] = useState("");
  const [messageUser, setMessageUser] = useState("");
  const [errorPassword, setErrorPassword] = useState("");
  const [errorUser, setErrorUser] = useState("");

  // Estados para troca de senha
  const [passData, setPassData] = useState({ 
    current_password: "", 
    new_password: "", 
    confirm_password: "" 
  });

  // Estados para criação de usuário
  const [newUserData, setNewUserData] = useState({ 
    username: "", 
    password: "" 
  });

  // Buscar informações do usuário autenticado
  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const response = await api.get("auth/me/");
        setIsStaff(response.data.is_staff);
      } catch (err) {
        console.error("Erro ao buscar informações do usuário:", err);
        setIsStaff(false);
      } finally {
        setLoadingUserInfo(false);
      }
    };

    fetchUserInfo();
  }, []);

  // Handler para troca de senha
  const handleChangePassword = async (e) => {
    e.preventDefault();
    setErrorPassword("");
    setMessagePassword("");

    // Validação
    if (!passData.current_password || !passData.new_password || !passData.confirm_password) {
      setErrorPassword("Todos os campos são obrigatórios");
      return;
    }

    if (passData.new_password !== passData.confirm_password) {
      setErrorPassword("As senhas não correspondem");
      return;
    }

    if (passData.new_password.length < 6) {
      setErrorPassword("A nova senha deve ter pelo menos 6 caracteres");
      return;
    }

    setLoadingPassword(true);
    try {
      await api.post("auth/change-password/", {
        current_password: passData.current_password,
        new_password: passData.new_password
      });
      setMessagePassword("Senha alterada com sucesso!");
      setPassData({ current_password: "", new_password: "", confirm_password: "" });
    } catch (err) {
      console.error(err);
      setErrorPassword(err.response?.data?.error || "Erro ao alterar senha. Verifique sua senha atual.");
    } finally {
      setLoadingPassword(false);
    }
  };

  // Handler para criação de usuário
  const handleCreateUser = async (e) => {
    e.preventDefault();
    setErrorUser("");
    setMessageUser("");

    if (!newUserData.username || !newUserData.password) {
      setErrorUser("Username e senha são obrigatórios");
      return;
    }

    if (newUserData.password.length < 6) {
      setErrorUser("A senha deve ter pelo menos 6 caracteres");
      return;
    }

    setLoadingUser(true);
    try {
      await api.post("auth/create-user/", newUserData);
      setMessageUser("Usuário criado com sucesso!");
      setNewUserData({ username: "", password: "" });
    } catch (err) {
      console.error(err);
      setErrorUser(err.response?.data?.error || "Erro ao criar usuário. Verifique se você tem permissão de administrador.");
    } finally {
      setLoadingUser(false);
    }
  };

  return (
    <section className="settings-page">
      <div className="settings-shell">
        <header className="settings-header">
          <h1>Configurações</h1>
        </header>

        <div className="settings-container">
          {/* Seção de Perfil */}
          <div className="settings-card">
            <h2>Perfil do Usuário</h2>
            <div className="profile-section">
              <div className="profile-field">
                <label className="field-label">Nome de usuário</label>
                <div className="field-value">{usuarioAtual}</div>
              </div>
            </div>
          </div>

          {/* Seção de Troca de Senha */}
          <div className="settings-card">
            <h2>Alterar Senha</h2>
            <p className="card-description">Altere sua senha de acesso à plataforma.</p>
            <form className="settings-form" onSubmit={handleChangePassword}>
              <div className="form-group">
                <label htmlFor="current-password" className="form-label">Senha Atual</label>
                <input 
                  id="current-password"
                  type="password" 
                  placeholder="Digite sua senha atual"
                  value={passData.current_password}
                  onChange={(e) => setPassData({...passData, current_password: e.target.value})}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label htmlFor="new-password" className="form-label">Nova Senha</label>
                <input 
                  id="new-password"
                  type="password" 
                  placeholder="Digite sua nova senha"
                  value={passData.new_password}
                  onChange={(e) => setPassData({...passData, new_password: e.target.value})}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label htmlFor="confirm-password" className="form-label">Confirmar Nova Senha</label>
                <input 
                  id="confirm-password"
                  type="password" 
                  placeholder="Confirme sua nova senha"
                  value={passData.confirm_password}
                  onChange={(e) => setPassData({...passData, confirm_password: e.target.value})}
                  className="form-input"
                />
              </div>
              {errorPassword && <div className="error-message">{errorPassword}</div>}
              {messagePassword && <div className="success-message">{messagePassword}</div>}
              <button type="submit" className="settings-btn primary" disabled={loadingPassword}>
                {loadingPassword ? "Alterando..." : "Alterar Senha"}
              </button>
            </form>
          </div>

          {/* Seção de Criação de Usuário (Admin) - visível apenas para staff */}
          {!loadingUserInfo && isStaff && (
            <div className="settings-card">
              <h2>Criar Novo Usuário</h2>
              <p className="card-description">Criar um novo acesso para colaborador. Você precisa ser administrador para realizar esta ação.</p>
              <form className="settings-form" onSubmit={handleCreateUser}>
                <div className="form-group">
                  <label htmlFor="new-username" className="form-label">Nome de Usuário</label>
                  <input 
                    id="new-username"
                    type="text" 
                    placeholder="Digite o novo nome de usuário"
                    value={newUserData.username}
                    onChange={(e) => setNewUserData({...newUserData, username: e.target.value})}
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="new-user-password" className="form-label">Senha Inicial</label>
                  <input 
                    id="new-user-password"
                    type="password" 
                    placeholder="Digite a senha inicial"
                    value={newUserData.password}
                    onChange={(e) => setNewUserData({...newUserData, password: e.target.value})}
                    className="form-input"
                  />
                </div>
                {errorUser && <div className="error-message">{errorUser}</div>}
                {messageUser && <div className="success-message">{messageUser}</div>}
                <button type="submit" className="settings-btn primary" disabled={loadingUser}>
                  {loadingUser ? "Criando..." : "Criar Usuário"}
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

export default Settings;