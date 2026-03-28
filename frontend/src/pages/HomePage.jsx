import { useNavigate } from "react-router-dom";
import { Camera, FileText, MessageCircle } from "lucide-react";

const actions = [
  {
    icon: Camera,
    title: "Проверка по фото",
    desc: "Сфотографируйте проблемную область",
    path: "/photo",
    color: "#2AABEE",
  },
  {
    icon: FileText,
    title: "Загрузить анализы",
    desc: "AI расшифрует результаты",
    path: "/lab",
    color: "#FF9800",
  },
  {
    icon: MessageCircle,
    title: "Описать симптомы",
    desc: "Чат с AI-ветеринаром",
    path: "/chat",
    color: "#4CAF50",
  },
];

export default function HomePage() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("vetai_user") || "{}");

  return (
    <div className="px-4 py-6">
      {/* Greeting */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold">
          Привет{user.petName ? `, ${user.petName}` : ""}! 🐾
        </h1>
        <p className="text-gray-500 mt-1">Как здоровье вашего питомца?</p>
      </div>

      {/* Beta banner */}
      <div className="mb-4 px-3 py-2 rounded-xl bg-green-50 border border-green-200 text-center text-sm text-green-700">
        Бета — бесплатно! Лимиты: 5 фото, 20 сообщений, 3 анализа в день
      </div>

      {/* Action cards */}
      <div className="space-y-3">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.path}
              onClick={() => navigate(action.path)}
              className="w-full flex items-center gap-4 p-4 rounded-2xl bg-white border border-gray-100 shadow-sm hover:shadow-md transition-shadow text-left"
            >
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center"
                style={{ background: `${action.color}15` }}
              >
                <Icon size={24} color={action.color} />
              </div>
              <div>
                <div className="font-semibold">{action.title}</div>
                <div className="text-sm text-gray-400">{action.desc}</div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Health tip */}
      <div className="mt-6 p-4 rounded-2xl bg-blue-50 border border-blue-100">
        <div className="text-sm font-semibold text-tg-blue mb-1">💡 Совет дня</div>
        <div className="text-sm text-gray-600">
          Регулярно проверяйте уши питомца — покраснение или запах могут указывать
          на отит. Загрузите фото для быстрой проверки!
        </div>
      </div>
    </div>
  );
}