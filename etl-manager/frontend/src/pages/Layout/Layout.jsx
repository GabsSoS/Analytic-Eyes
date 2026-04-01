import { Outlet } from "react-router-dom";
import Header from "../../components/Header";
import Sidebar from "../../components/Sidebar";


function Layout() {
  return (
    <>
      <Header />
      <div style={{ display: "flex" }}>
        <Sidebar />

        <main>
          <Outlet />
        </main>
      </div>
    </>
  );
}

export default Layout;