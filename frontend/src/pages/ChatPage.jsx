import { useState, useRef, useEffect } from "react";
import { Send, Loader2, MapPin } from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function ChatPage() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Здравствуйте! Я AI-ветеринар VetAI. Опишите симптомы вашего питомца, и я помогу разобраться. Что вас беспокоит?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef();

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const user = JSON.parse(localStorage.getItem("vetai_user") || "{}");

      const telegramId = localStorage.getItem("vetai_telegram_id") || "12345";

      const res = await fetch(`${API_URL}/api/v1/chat/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-telegram-id": telegramId,
        },
        body: JSON.stringify({
          message: userMsg.content,
          history: messages.map((m) => ({ role: m.role, content: m.content })),
          city: user.city || null,
        }),
      });

      if (res.status === 429) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "Лимит 3 запроса в день исчерпан. Попробуйте завтра." },
        ]);
        return;
      }

      const data = await res.json();

      // Add assistant reply
      setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);

      // If clinic recommendation exists, add it as a separate message
      if (data.clinic_recommendation) {
        setMessages((prev) => [
          ...prev,
          { role: "clinic", content: data.clinic_recommendation },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Извините, произошла ошибка. Попробуйте ещё раз." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const renderMessage = (msg, i) => {
    if (msg.role === "clinic") {
      // Extract URL from the message
      const urlMatch = msg.content.match(/(https:\/\/yandex\.ru\/maps\/[^\s]+)/);
      const url = urlMatch ? urlMatch[1] : null;
      const textParts = msg.content.split(url || "---no-split---");

      return (
        <div key={i} className="flex justify-start">
          <div className="max-w-[85%] px-4 py-3 rounded-2xl rounded-bl-sm bg-red-50 border border-red-200 text-sm">
            <div className="flex items-center gap-2 text-red-600 font-semibold mb-1">
              <MapPin size={16} />
              Рекомендация
            </div>
            <div className="text-gray-700 whitespace-pre-line">
              {url ? (
                <>
                  {textParts[0]}
                  <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-tg-blue underline font-medium"
                  >
                    Открыть карту клиник
                  </a>
                  {textParts[1]}
                </>
              ) : (
                msg.content
              )}
            </div>
          </div>
        </div>
      );
    }

    return (
      <div
        key={i}
        className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
      >
        <div
          className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-line ${
            msg.role === "user"
              ? "bg-tg-blue text-white rounded-br-sm"
              : "bg-gray-100 text-gray-800 rounded-bl-sm"
          }`}
        >
          {msg.content}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.map(renderMessage)}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-bl-sm">
              <Loader2 className="animate-spin text-gray-400" size={18} />
            </div>
          </div>
        )}
        <div ref={scrollRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 px-4 py-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Опишите симптомы..."
          className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 focus:border-tg-blue focus:outline-none text-sm"
        />
        <button
          onClick={sendMessage}
          disabled={!input.trim() || loading}
          className="bg-tg-blue text-white w-10 h-10 rounded-xl flex items-center justify-center disabled:opacity-50"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
