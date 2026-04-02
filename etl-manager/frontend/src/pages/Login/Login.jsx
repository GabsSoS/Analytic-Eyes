import "./Login.css"
import OndaEsquerda from '../../assets/Login/onda-esquerda.png'
import OndaDireita from '../../assets/Login/onda-direita.png'
import CartoonImage from '../../assets/Login/rafiki.png'
import Logo from '../../assets/Login/Logo1.png'
import User from '../../assets/Login/user 1.png'
import PasswordIcon from '../../assets/Login/eye-scanner 1.png'

function Login() {
  function handleSubmit() {
    
    username = document.querySelector('.email').value;
    password = document.querySelector('.password').value;

    
    
    // Aqui você pode adicionar a lógica para autenticar o usuário
  }


  return (
    <div className="background">
      <div className="onda-esquerda">
        <img src={OndaEsquerda} alt="Onda decorativa esquerda" />
      </div>

      <section className="campo-login">
        <img src={Logo} alt="Logo da empresa" className="logo" />

        <form className="login-form">
          <div className="email-input-container">
            <img src={User} alt="Ícone de usuário" className="user-icon" />
            <input 
              className="email" 
              type="email" 
              placeholder="Digite o seu Username" 
              required 
            />
          </div>
          <div className="password-input-container">
            <img src={PasswordIcon} alt="Ícone de senha" className="password-icon" />
            <input 
              className="password" 
              type="password" 
              placeholder="Digite a sua senha" 
              required 
            />
          </div>

          <button onClick={handleSubmit} type="submit" className="login-button">Entrar</button>
        </form>
      </section>

      <img className="foto-walpaper" src={CartoonImage} alt="Cartoon ilustrativo" />

      <div className="onda-direita">
        <img src={OndaDireita} alt="Onda decorativa direita" />
      </div>
    </div>
  );
}

export default Login