import { Link } from 'react-router-dom'

function Header() {
  return (
    <nav>
      <Link to="/">Dashboard</Link>
      <Link to="/jobs">Jobs</Link>
      <Link to="/settings">Settings</Link>
    </nav>
  )
}

export default Header