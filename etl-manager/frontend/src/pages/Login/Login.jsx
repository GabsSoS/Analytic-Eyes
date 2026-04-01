import "./Login.css"
import OndaEsquerda from '../../assets/Login/onda-esquerda.png'
import OndaDireita from '../../assets/Login/onda-direita.png'
import CartoonImage from '../../assets/Login/rafiki.png'

function Login() {
  return (
  <div className="background">
    <h1>teste</h1>
    <div className="onda-esquerda">
      <img src={OndaEsquerda} alt="" />



    </div>
        <div className="onda-direita">
      <img src={OndaDireita} alt="" />
    </div>




  
  </div>
  );
}

export default Login