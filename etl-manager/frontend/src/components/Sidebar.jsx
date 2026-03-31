import { Link } from "react-router-dom";
import "./Sidebar.css";

function Sidebar() {
  return (
    <aside className="sidebar">
      <h2>ETL</h2>
      <nav>
        <Link to="/">Dashboard</Link>
        <Link to="/jobs">Jobs</Link>
        <Link to="/settings">Settings</Link>
      </nav>
    </aside>
  );
}

export default Sidebar;