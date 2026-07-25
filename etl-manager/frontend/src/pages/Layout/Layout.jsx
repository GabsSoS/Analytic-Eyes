import { Outlet } from "react-router-dom";
import Header from "../../components/Header";
import Sidebar from "../../components/Sidebar";
import OnboardingTour from "../../components/OnboardingTour";
import { TourProvider } from "../../context/TourContext";
import "./Layout.css";

function Layout() {
  return (
    <TourProvider>
      <div className="app-shell">
        <Header />
        <Sidebar />
        <main className="app-main">
          <Outlet />
        </main>
        <OnboardingTour />
      </div>
    </TourProvider>
  );
}

export default Layout;
