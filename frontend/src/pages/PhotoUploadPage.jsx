import { useState, useRef } from "react";
import { Camera, Upload, Loader2 } from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const HINTS = [
  "чешется", "рана", "опухоль/шишка", "выпадает шерсть",
  "покраснение", "гноится", "хромает", "отёк",
  "появилось недавно", "после еды", "после прогулки", "после укуса",
];

export default function PhotoUploadPage() {
  const [photo, setPhoto] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [complaint, setComplaint] = useState("");
  const [selectedHints, setSelectedHints] = useState([]);
  const fileRef = useRef();

  const handleFile = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setPhoto(file);
    setPreview(URL.createObjectURL(file));
    setResult(null);
  };

  const toggleHint = (hint) => {
    setSelectedHints((prev) =>
      prev.includes(hint) ? prev.filter((h) => h !== hint) : [...prev, hint]
    );
  };

  const [limitError, setLimitError] = useState(null);

  const analyze = async () => {
    if (!photo) return;
    setLoading(true);
    setLimitError(null);
    try {
      const telegramId = localStorage.getItem("vetai_telegram_id") || "12345";
      const user = JSON.parse(localStorage.getItem("vetai_user") || "{}");
      const petSpecies = user.petType === "dog" ? "собаки" : user.petType === "cat" ? "кошки" : "питомца";

      // Build context string from complaint + hints
      const context = [complaint.trim(), ...selectedHints].filter(Boolean).join(", ");

      const form = new FormData();
      form.append("photo", photo);
      form.append("species", petSpecies);
      if (context) form.append("complaint", context);
      if (user.city) form.append("city", user.city);

      const res = await fetch(`${API_URL}/api/v1/diagnosis/photo`, {
        method: "POST",
        headers: { "x-telegram-id": telegramId },
        body: form,
      });

      if (res.status === 429) {
        setLimitError("Дневной лимит исчерпан. Попробуйте завтра.");
        return;
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="px-4 py-6">
      <h1 className="text-xl font-bold mb-4 text-gray-900">Проверка по фото</h1>
      <p className="text-sm text-gray-600 mb-6">
        Сфотографируйте проблемное место питомца. AI определит возможное заболевание.
      </p>

      {/* Upload area */}
      {!preview ? (
        <button
          onClick={() => fileRef.current.click()}
          className="w-full h-48 border-2 border-dashed border-gray-300 rounded-2xl flex flex-col items-center justify-center gap-3 text-gray-400 hover:border-tg-blue hover:text-tg-blue transition-colors bg-white"
        >
          <Camera size={40} />
          <span className="font-medium text-sm text-gray-900">Загрузить фото</span>
          <span className="text-xs text-gray-400">Камера или галерея</span>
        </button>
      ) : (
        <div className="relative">
          <img
            src={preview}
            alt="Pet photo"
            className="w-full h-48 object-cover rounded-2xl"
          />
          <button
            onClick={() => { setPreview(null); setPhoto(null); setResult(null); setComplaint(""); setSelectedHints([]); }}
            className="absolute top-2 right-2 bg-black/50 text-white w-8 h-8 rounded-full flex items-center justify-center"
          >
            ✕
          </button>
        </div>
      )}

      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        onChange={handleFile}
        className="hidden"
      />

      {/* Complaint + hints — show after photo selected, before result */}
      {preview && !result && (
        <>
          <div className="mt-4">
            <input
              type="text"
              value={complaint}
              onChange={(e) => setComplaint(e.target.value)}
              placeholder="Опишите проблему (необязательно)"
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-tg-blue focus:outline-none text-sm text-gray-900"
            />
          </div>

          <div className="mt-2 flex flex-wrap gap-2">
            {HINTS.map((hint) => (
              <button
                key={hint}
                onClick={() => toggleHint(hint)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                  selectedHints.includes(hint)
                    ? "bg-tg-blue text-white"
                    : "bg-gray-100 text-gray-600"
                }`}
              >
                {hint}
              </button>
            ))}
          </div>

          <button
            onClick={analyze}
            disabled={loading}
            className="w-full mt-4 bg-tg-blue text-white font-semibold py-3 rounded-xl flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? <Loader2 className="animate-spin" size={20} /> : <Upload size={20} />}
            {loading ? "Анализируем..." : "Проверить"}
          </button>
        </>
      )}

      {/* Limit error */}
      {limitError && (
        <div className="mt-4 p-4 rounded-2xl bg-red-50 border border-red-200 text-center text-sm text-red-600 font-medium">
          {limitError}
        </div>
      )}

      {/* Result */}
      {result && result.condition === "not_animal" ? (
        <div className="mt-4 p-4 rounded-2xl bg-orange-50 border border-orange-200 shadow-sm text-center">
          <span className="font-bold text-lg text-orange-600">Животное не найдено</span>
          <p className="text-sm text-orange-700 mt-2">
            Пожалуйста, загрузите фото вашего питомца
          </p>
        </div>
      ) : result && (
        <div className="mt-4 p-4 rounded-2xl bg-white border border-gray-100 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="font-bold text-lg text-gray-900">{result.condition}</span>
            <span
              className={`text-xs font-semibold px-2 py-1 rounded-full ${
                result.severity === "high"
                  ? "bg-red-100 text-red-600"
                  : result.severity === "medium"
                  ? "bg-yellow-100 text-yellow-700"
                  : "bg-green-100 text-green-600"
              }`}
            >
              {result.severity === "high" ? "Срочно" : result.severity === "medium" ? "Внимание" : "Норма"}
            </span>
          </div>
          <p className="text-sm text-gray-600 mb-3">{result.description}</p>
          <p className="text-sm font-medium text-tg-blue">{result.recommendation}</p>
          <div className="mt-3 text-xs text-gray-400">
            Уверенность: {Math.round(result.confidence * 100)}%
          </div>
        </div>
      )}
    </div>
  );
}
