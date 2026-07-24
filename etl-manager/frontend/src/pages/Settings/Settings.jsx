import "./Settings.css";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../services/api";

function Settings() {
  const navigate = useNavigate();
  const [usuarioAtual] = useState(localStorage.getItem("username") || "Usuário");
  const avatarInitial = usuarioAtual.charAt(0).toUpperCase() || "?";
  const [isStaff, setIsStaff] = useState(false);
  const [isSuperuser, setIsSuperuser] = useState(false);
  const [currentUserId, setCurrentUserId] = useState(null);
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
    password: "",
    is_staff: false
  });

  // Estados para gerenciamento de usuários (admin)
  const [usersList, setUsersList] = useState([]);
  const [loadingUsersList, setLoadingUsersList] = useState(false);
  const [userManageError, setUserManageError] = useState("");
  const [userManageMessage, setUserManageMessage] = useState("");
  const [resetPasswordOpenId, setResetPasswordOpenId] = useState(null);
  const [resetPasswordValue, setResetPasswordValue] = useState("");
  const [userActionLoadingId, setUserActionLoadingId] = useState(null);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    navigate("/login"); 
  };

  // Busca a lista de usuários (com is_staff/is_active) para a tela de
  // gerenciamento - só staff recebe esses campos extras do backend.
  const fetchUsersList = async () => {
    setLoadingUsersList(true);
    try {
      const response = await api.get("users/");
      setUsersList(response.data.users || []);
    } catch (err) {
      console.error("Erro ao buscar lista de usuários:", err);
    } finally {
      setLoadingUsersList(false);
    }
  };

  // Buscar informações do usuário autenticado
  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const response = await api.get("auth/me/");
        setIsStaff(response.data.is_staff);
        setIsSuperuser(response.data.is_superuser);
        setCurrentUserId(response.data.id);
        if (response.data.is_staff) {
          fetchUsersList();
        }
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
      setErrorUser("Nome de usuário e senha são obrigatórios");
      return;
    }

    if (newUserData.password.length < 6) {
      setErrorUser("A senha deve ter pelo menos 6 caracteres");
      return;
    }

    setLoadingUser(true);
    try {
      await api.post("auth/create-user/", newUserData);
      setMessageUser(
        newUserData.is_staff
          ? "Usuário administrador criado com sucesso!"
          : "Usuário criado com sucesso!"
      );
      setNewUserData({ username: "", password: "", is_staff: false });
      if (isStaff) fetchUsersList();
    } catch (err) {
      console.error(err);
      setErrorUser(err.response?.data?.error || "Erro ao criar usuário. Verifique se você tem permissão de administrador.");
    } finally {
      setLoadingUser(false);
    }
  };

  // Handler para promover/remover administrador
  const handleToggleStaff = async (userId) => {
    setUserManageError("");
    setUserManageMessage("");
    setUserActionLoadingId(userId);
    try {
      const response = await api.post(`users/${userId}/toggle-staff/`);
      setUserManageMessage(
        response.data.is_staff
          ? `${response.data.username} agora é administrador.`
          : `${response.data.username} não é mais administrador.`
      );
      await fetchUsersList();
    } catch (err) {
      console.error(err);
      setUserManageError(err.response?.data?.error || "Erro ao alterar permissão de administrador.");
    } finally {
      setUserActionLoadingId(null);
    }
  };

  // Handler para ativar/desativar conta ("excluir conta" = desativar,
  // preserva as pipelines existentes da pessoa em vez de apagar tudo)
  const handleToggleActive = async (userId) => {
    setUserManageError("");
    setUserManageMessage("");
    setUserActionLoadingId(userId);
    try {
      const response = await api.post(`users/${userId}/toggle-active/`);
      setUserManageMessage(
        response.data.is_active
          ? `${response.data.username} foi reativado.`
          : `${response.data.username} foi desativado.`
      );
      await fetchUsersList();
    } catch (err) {
      console.error(err);
      setUserManageError(err.response?.data?.error || "Erro ao ativar/desativar conta.");
    } finally {
      setUserActionLoadingId(null);
    }
  };

  // Handler para redefinir a senha de outro usuário
  const handleResetPassword = async (userId, e) => {
    e.preventDefault();
    setUserManageError("");
    setUserManageMessage("");

    if (!resetPasswordValue || resetPasswordValue.length < 6) {
      setUserManageError("A nova senha deve ter pelo menos 6 caracteres");
      return;
    }

    setUserActionLoadingId(userId);
    try {
      const response = await api.post(`users/${userId}/reset-password/`, {
        new_password: resetPasswordValue,
      });
      setUserManageMessage(response.data.message);
      setResetPasswordOpenId(null);
      setResetPasswordValue("");
    } catch (err) {
      console.error(err);
      setUserManageError(err.response?.data?.error || "Erro ao redefinir senha.");
    } finally {
      setUserActionLoadingId(null);
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
              <div className="profile-avatar" aria-hidden="true">{avatarInitial}</div>
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
                <div className="form-group form-group-checkbox">
                  <label htmlFor="new-user-is-staff" className="checkbox-label">
                    <input
                      id="new-user-is-staff"
                      type="checkbox"
                      checked={newUserData.is_staff}
                      onChange={(e) => setNewUserData({...newUserData, is_staff: e.target.checked})}
                    />
                    Esta conta será administradora
                  </label>
                </div>
                {errorUser && <div className="error-message">{errorUser}</div>}
                {messageUser && <div className="success-message">{messageUser}</div>}
                <button type="submit" className="settings-btn primary" disabled={loadingUser}>
                  {loadingUser ? "Criando..." : "Criar Usuário"}
                </button>
              </form>
            </div>
          )}

          {/* Seção de Gerenciamento de Usuários (Admin) - visível apenas para staff */}
          {!loadingUserInfo && isStaff && (
            <div className="settings-card">
              <h2>Gerenciar Usuários</h2>
              <p className="card-description">
                Promova ou remova administradores, desative contas ou redefina a senha de outras pessoas.
              </p>

              {userManageError && <div className="error-message">{userManageError}</div>}
              {userManageMessage && <div className="success-message">{userManageMessage}</div>}

              {loadingUsersList ? (
                <p className="card-description">Carregando usuários...</p>
              ) : (
                <div className="user-manage-list">
                  {usersList.map((u) => {
                    const isSelf = u.id === currentUserId;
                    const isBusy = userActionLoadingId === u.id;
                    // Espelha a regra do backend: mexer no admin/senha/ativação
                    // de OUTRO administrador exige superusuário. Promover um
                    // usuário comum a admin continua liberado pra qualquer staff.
                    const needsSuperuserToActOnTarget = u.is_staff && !isSelf && !isSuperuser;
                    const restrictedTitle = "Apenas um superusuário pode fazer isso com outro administrador";

                    return (
                      <div key={u.id} className="user-manage-row">
                        <div className="user-manage-info">
                          <span className="user-manage-name">{u.username}</span>
                          <span className="user-manage-badges">
                            {u.is_staff && <span className="user-badge user-badge-admin">Administrador</span>}
                            {!u.is_active && <span className="user-badge user-badge-inactive">Desativado</span>}
                            {isSelf && <span className="user-badge user-badge-self">Você</span>}
                          </span>
                        </div>

                        <div className="user-manage-actions">
                          <button
                            type="button"
                            className="user-manage-btn"
                            disabled={isBusy || (u.is_staff && needsSuperuserToActOnTarget)}
                            title={u.is_staff && needsSuperuserToActOnTarget ? restrictedTitle : undefined}
                            onClick={() => handleToggleStaff(u.id)}
                          >
                            {u.is_staff ? "Remover admin" : "Tornar admin"}
                          </button>
                          <button
                            type="button"
                            className="user-manage-btn"
                            disabled={isBusy || needsSuperuserToActOnTarget}
                            title={needsSuperuserToActOnTarget ? restrictedTitle : undefined}
                            onClick={() => {
                              setResetPasswordOpenId(resetPasswordOpenId === u.id ? null : u.id);
                              setResetPasswordValue("");
                              setUserManageError("");
                            }}
                          >
                            Redefinir senha
                          </button>
                          <button
                            type="button"
                            className="user-manage-btn danger"
                            disabled={isBusy || isSelf || needsSuperuserToActOnTarget}
                            title={isSelf ? "Você não pode desativar sua própria conta" : (needsSuperuserToActOnTarget ? restrictedTitle : undefined)}
                            onClick={() => handleToggleActive(u.id)}
                          >
                            {u.is_active ? "Desativar" : "Reativar"}
                          </button>
                        </div>

                        {resetPasswordOpenId === u.id && (
                          <form
                            className="user-reset-form"
                            onSubmit={(e) => handleResetPassword(u.id, e)}
                          >
                            <input
                              type="password"
                              placeholder="Nova senha (mín. 6 caracteres)"
                              value={resetPasswordValue}
                              onChange={(e) => setResetPasswordValue(e.target.value)}
                              className="form-input"
                              autoFocus
                            />
                            <button type="submit" className="settings-btn primary" disabled={isBusy}>
                              Confirmar
                            </button>
                          </form>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Sair da conta */}
          <div className="settings-card settings-card-danger">
            <h2>Sair da conta</h2>
            <p className="card-description">Encerra sua sessão atual e retorna para a tela de login.</p>
            <button
              type="button"
              className="settings-btn danger"
              onClick={handleLogout}
            >
              Sair
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

export default Settings;