import React from "react";
import { Link, useLocation } from "react-router-dom";

interface NavItem {
    path: string;
    label: string;
    icon: string;
}

const navItems: NavItem[] = [
    { path: "/", label: "Dashboard", icon: "📊" },
    { path: "/json", label: "JSON View", icon: "📄" },
    { path: "/analytics", label: "Analytics", icon: "📈" },
    { path: "/settings", label: "Settings", icon: "⚙️" },
    { path: "/about", label: "About", icon: "ℹ️" },
];

export const Sidebar: React.FC = () => {
    const location = useLocation();

    return (
        <div className="w-64 bg-white border-r border-gray-200 min-h-screen flex flex-col">
            {/* Logo/Header */}
            <div className="p-6 border-b border-gray-200">
                <h1 className="text-xl font-bold text-gray-900">Polymarket</h1>
                <p className="text-xs text-gray-500 mt-1">Real-Time Data</p>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4">
                <ul className="space-y-2">
                    {navItems.map(item => {
                        const isActive = location.pathname === item.path;
                        return (
                            <li key={item.path}>
                                <Link
                                    to={item.path}
                                    className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                                        isActive
                                            ? "bg-blue-50 text-blue-700 font-medium"
                                            : "text-gray-700 hover:bg-gray-50"
                                    }`}
                                >
                                    <span className="text-xl">{item.icon}</span>
                                    <span>{item.label}</span>
                                </Link>
                            </li>
                        );
                    })}
                </ul>
            </nav>

            {/* Footer */}
            <div className="p-4 border-t border-gray-200">
                <div className="text-xs text-gray-500 text-center">v1.0.0</div>
            </div>
        </div>
    );
};
