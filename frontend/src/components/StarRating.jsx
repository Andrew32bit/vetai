import { useState } from "react";
import { Star } from "lucide-react";
import { t } from "../i18n";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function StarRating({ diagnosisId }) {
  const [rating, setRating] = useState(0);
  const [hover, setHover] = useState(0);
  const [sent, setSent] = useState(false);

  const submit = async (value) => {
    setRating(value);
    setSent(true);
    try {
      const telegramId = localStorage.getItem("vetai_telegram_id") || "12345";
      await fetch(`${API_URL}/api/v1/diagnosis/rate/${diagnosisId}?rating=${value}`, {
        method: "POST",
        headers: { "x-telegram-id": telegramId },
      });
    } catch (err) {
      console.error("Rating error:", err);
    }
  };

  if (sent) {
    return (
      <div className="mt-3 text-center text-sm text-gray-400">
        {t("ratingThanks")} {"★".repeat(rating)}{"☆".repeat(5 - rating)}
      </div>
    );
  }

  return (
    <div className="mt-3 text-center">
      <p className="text-xs text-gray-400 mb-1">{t("ratingPrompt")}</p>
      <div className="flex justify-center gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onClick={() => submit(star)}
            onMouseEnter={() => setHover(star)}
            onMouseLeave={() => setHover(0)}
            className="p-1"
          >
            <Star
              size={24}
              className={
                star <= (hover || rating)
                  ? "fill-yellow-400 text-yellow-400"
                  : "text-gray-300"
              }
            />
          </button>
        ))}
      </div>
    </div>
  );
}
