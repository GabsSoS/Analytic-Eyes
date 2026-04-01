import { Link } from "react-router-dom";
import "./Sidebar.css";

function Sidebar() {
  return (
    <aside className="sidebar">
      <h2>ETL</h2>
      <nav>
        <Link to="/home">Home</Link>
        <Link to="/fluxos">Fluxos</Link>
        <Link to="/details">Details</Link>
        <Link to="/settings">Settings</Link>
      </nav>
    </aside>
  );
}

export default Sidebar;