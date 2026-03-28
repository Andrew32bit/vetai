import { useLocation, useNavigate } from "react-router-dom";
import { Home, Camera, FileText, MessageCircle, Clock } from "lucide-react";

const tabs = [
  { path: "/", icon: Home, label: "Главная" },
  { path: "/photo", icon: Camera, label: "Фото" },
  { path: "/lab", icon: FileText, label: "Анализы" },
  { path: "/chat", icon: MessageCircle, label: "Чат" },
  { path: "/history", icon: Clock, label: "История" },
];

export default function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <nav className="flex items-center justify-around border-t border-gray-200 bg-white py-2 px-1">
      {tabs.map((tab) => {
        const isActive = location.pathname === tab.path;
        const Icon = tab.icon;
        return (
          <button
            key={tab.path}
            onClick={() => navigate(tab.path)}
            className={`flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg transition-colors ${
              isActive ? "text-tg-blue" : "text-gray-400"
            }`}
          >
            <Icon size={22} strokeWidth={isActive ? 2.5 : 1.5} />
            <span className="text-[10px] font-medium">{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
}