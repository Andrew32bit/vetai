import { useState } from "react";
import { PawPrint, Cat, Dog } from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const steps = ["welcome", "pet_type", "pet_details", "plan"];

export default function OnboardingPage({ onComplete }) {
  const [step, setStep] = useState(0);
  const [petType, setPetType] = useState(null); // "cat" | "dog"
  const [petName, setPetName] = useState("");
  const [breed, setBreed] = useState("");
  const [city, setCity] = useState("");
  // plan is always "beta" during beta period

  const next = () => setStep((s) => Math.min(s + 1, steps.length - 1));
  const current = steps[step];

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-6 bg-gradient-to-b from-blue-50 to-white">
      {/* Progress dots */}
      <div className="flex gap-2 mb-8">
        {steps.map((_, i) => (
          <div
            key={i}
            className={`w-2.5 h-2.5 rounded-full transition-colors ${
              i <= step ? "bg-tg-blue" : "bg-gray-200"
            }`}
          />
        ))}
      </div>

      {current === "welcome" && (
        <div className="text-center">
          <div className="text-6xl mb-4">🐾</div>
          <h1 className="text-2xl font-bold mb-2">VetAI</h1>
          <p className="text-gray-500 mb-8">
            AI-ветеринар в вашем телефоне. Проверьте здоровье питомца по фото, анализам или симптомам.
          </p>
          <button
            onClick={next}
            className="bg-tg-blue text-white font-semibold px-8 py-3 rounded-xl text-lg"
          >
            Начать
          </button>
        </div>
      )}

      {current === "pet_type" && (
        <div className="text-center w-full max-w-sm">
          <h2 className="text-xl font-bold mb-6">Кто ваш питомец?</h2>
          <div className="flex gap-4 justify-center">
            {[
              { type: "cat", emoji: "🐱", label: "Кошка" },
              { type: "dog", emoji: "🐶", label: "Собака" },
            ].map((opt) => (
              <button
                key={opt.type}
                onClick={() => { setPetType(opt.type); next(); }}
                className={`flex flex-col items-center gap-2 p-6 rounded-2xl border-2 transition-all flex-1 ${
                  petType === opt.type ? "border-tg-blue bg-blue-50" : "border-gray-200"
                }`}
              >
                <span className="text-5xl">{opt.emoji}</span>
                <span className="font-semibold">{opt.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {current === "pet_details" && (
        <div className="w-full max-w-sm">
          <h2 className="text-xl font-bold mb-6 text-center">Расскажите о питомце</h2>
          <div className="space-y-4">
            <input
              type="text"
              placeholder="Имя питомца"
              value={petName}
              onChange={(e) => setPetName(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-tg-blue focus:outline-none"
            />
            <input
              type="text"
              placeholder="Порода (необязательно)"
              value={breed}
              onChange={(e) => setBreed(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-tg-blue focus:outline-none"
            />
            <input
              type="text"
              placeholder="Ваш город (для поиска клиник)"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-tg-blue focus:outline-none"
            />
            <button
              onClick={next}
              disabled={!petName}
              className="w-full bg-tg-blue text-white font-semibold py-3 rounded-xl disabled:opacity-50"
            >
              Далее
            </button>
          </div>
        </div>
      )}

      {current === "plan" && (
        <div className="w-full max-w-sm text-center">
          <h2 className="text-xl font-bold mb-4">Бета-версия — все функции бесплатны!</h2>
          <div className="p-4 rounded-xl bg-blue-50 border border-blue-100 mb-4">
            <div className="text-sm font-semibold text-tg-blue mb-2">Дневной лимит:</div>
            <div className="text-sm text-gray-700">
              3 запроса в день (фото + чат + анализы)
            </div>
          </div>
          <p className="text-xs text-gray-400 mb-6">
            После завершения бета-тестирования будет введена платная подписка
          </p>
          <button
            onClick={async () => {
              const telegramId = localStorage.getItem("vetai_telegram_id") || "12345";
              try {
                await fetch(`${API_URL}/api/v1/users/register`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    telegram_id: Number(telegramId),
                    pet: { name: petName, species: petType, breed: breed || null },
                    city: city || null,
                  }),
                });
              } catch (err) {
                console.error("Register error:", err);
              }
              onComplete({ petType, petName, breed, city, plan: "beta" });
            }}
            className="w-full bg-tg-blue text-white font-semibold py-3 rounded-xl"
          >
            Начать использовать
          </button>
        </div>
      )}
    </div>
  );
}