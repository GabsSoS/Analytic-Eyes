import { Link } from "react-router-dom";
import Menu from "../assets/components/Menu 1.png";
import "./Sidebar.css";

function Sidebar() {
  return (
    <aside className="sidebar">
      
      <nav>
      <img src={Menu} alt="Recolher Menu" className="icons" />
        {/* <Link to="/home">Home</Link>
        <Link to="/fluxos">Fluxos</Link>
        <Link to="/details">Details</Link>
        <Link to="/settings">Settings</Link> */}
      </nav>
    </aside>
  );
}

export default Sidebar;