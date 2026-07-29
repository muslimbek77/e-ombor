import { Outlet } from "react-router-dom";
import Header from "./Header";
import Sidebar from "./Sidebar";

const Layout = () => {
  return (
    <>
      <div className="min-h-screen flex items-stretch">
        <Sidebar />

        <div
          className="flex-1 flex flex-col p-2.5"
          style={{
            background: "linear-gradient(135deg, #16a34a 0%, #15803d 100%)",
          }}
        >
          <Header />

          <main className="flex-1 p-6 bg-white rounded-b-2xl">
            <Outlet />
          </main>
        </div>
      </div>
    </>
  );
};

export default Layout;
