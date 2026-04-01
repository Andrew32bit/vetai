import { useLocation, useNavigate } from "react-router-dom";
import { Home, Camera, FileText, MessageCircle, Clock } from "lucide-react";
import { t } from "../i18n";

const tabDefs = [
  { path: "/", icon: Home, labelKey: "navHome" },
  { path: "/photo", icon: Camera, labelKey: "navPhoto" },
  { path: "/lab", icon: FileText, labelKey: "navLab" },
  { path: "/chat", icon: MessageCircle, labelKey: "navChat" },
  { path: "/history", icon: Clock, labelKey: "navHistory" },
];

export default function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <nav className="flex items-center justify-around border-t border-gray-200 bg-white py-2 px-1">
      {tabDefs.map((tab) => {
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
            <span className="text-[10px] font-medium">{t(tab.labelKey)}</span>
          </button>
        );
      })}
    </nav>
  );
}
