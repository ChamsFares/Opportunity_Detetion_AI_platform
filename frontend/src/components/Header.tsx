import React from "react";
import { Link, useLocation } from "react-router-dom";
import { Target, BarChart3, FileText, Lightbulb, Map } from "lucide-react";

const Header: React.FC = () => {
  const location = useLocation();
  const isHome = location.pathname === "/";

  const navItems = [
    { path: "/dashboard", icon: BarChart3, label: "Dashboard" },
    { path: "/report", icon: FileText, label: "Report" },
    { path: "/recommendations", icon: Lightbulb, label: "Recommendations" },
    { path: "/map", icon: Map, label: "Mapping" },
  ];

  if (isHome || location.pathname === "/analysis") {
    return (
      <header className="bg-white/80 backdrop-blur-sm border-b border-slate-200/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center h-16">
            <Link to="/" className="flex items-center space-x-3">
              <img
                src="/logo_opportuna2.png"
                alt="Opportuna Logo"
                className="w-22 h-12"
              />
              <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-emerald-600 bg-clip-text text-transparent">
                OPPORTUNA
              </span>
            </Link>
          </div>
        </div>
      </header>
    );
  }

  return (
    <header className="bg-white/80 backdrop-blur-sm border-b border-slate-200/50 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-3">
            <img
              src="/logo_opportuna2.png"
              alt="Opportuna Logo"
              className="w-22 h-12"
            />
            <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-emerald-600 bg-clip-text text-transparent">
              OPPORTUNA
            </span>
          </Link>
          <nav className="flex items-center space-x-1">
            {navItems.map(({ path, icon: Icon, label }) => (
              <Link
                key={path}
                to={path}
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  location.pathname === path
                    ? "bg-blue-100 text-blue-700"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="hidden sm:inline">{label}</span>
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
