import { useState } from "react";

const screens = {
  ONBOARDING: "onboarding",
  HOME: "home",
  UPLOAD_PHOTO: "upload_photo",
  UPLOAD_ANALYSIS: "upload_analysis",
  SYMPTOM_CHAT: "symptom_chat",
  DIAGNOSIS: "diagnosis",
  HISTORY: "history",
  PROFILE: "profile",
};

// Telegram-style phone frame
function PhoneFrame({ children, title, onBack }) {
  return (
    <div
      style={{
        width: 375,
        height: 740,
        borderRadius: 40,
        border: "8px solid #1a1a2e",
        background: "#fff",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        boxShadow: "0 20px 60px rgba(0,0,0,0.3)",
        position: "relative",
      }}
    >
      {/* Status bar */}
      <div
        style={{
          background: "#2AABEE",
          padding: "8px 20px 0",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: 12,
          color: "#fff",
          fontWeight: 500,
        }}
      >
        <span>9:41</span>
        <span style={{ fontSize: 10 }}>Telegram Mini App</span>
        <span>100%</span>
      </div>
      {/* Telegram header */}
      <div
        style={{
          background: "#2AABEE",
          padding: "10px 16px 14px",
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}
      >
        {onBack && (
          <button
            onClick={onBack}
            style={{
              background: "none",
              border: "none",
              color: "#fff",
              fontSize: 22,
              cursor: "pointer",
              padding: 0,
              lineHeight: 1,
            }}
          >
            &#8592;
          </button>
        )}
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: 18,
            background: "rgba(255,255,255,0.2)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 18,
          }}
        >
          🐾
        </div>
        <div>
          <div
            style={{
              color: "#fff",
              fontSize: 16,
              fontWeight: 600,
              lineHeight: 1.2,
            }}
          >
            {title || "VetAI"}
          </div>
          <div
            style={{
              color: "rgba(255,255,255,0.7)",
              fontSize: 12,
              lineHeight: 1.2,
            }}
          >
            AI-ветеринар онлайн
          </div>
        </div>
      </div>
      {/* Content */}
      <div style={{ flex: 1, overflow: "auto", background: "#e8ecf0" }}>
        {children}
      </div>
    </div>
  );
}

function ChatBubble({ from, children, time }) {
  const isBot = from === "bot";
  return (
    <div
      style={{
        display: "flex",
        justifyContent: isBot ? "flex-start" : "flex-end",
        padding: "2px 12px",
      }}
    >
      <div
        style={{
          maxWidth: "80%",
          background: isBot ? "#fff" : "#EFFDDE",
          borderRadius: isBot ? "4px 18px 18px 18px" : "18px 4px 18px 18px",
          padding: "8px 12px",
          fontSize: 14,
          lineHeight: 1.45,
          color: "#000",
          boxShadow: "0 1px 1px rgba(0,0,0,0.06)",
        }}
      >
        {children}
        <div
          style={{
            fontSize: 11,
            color: "#999",
            textAlign: "right",
            marginTop: 2,
          }}
        >
          {time || "сейчас"}
        </div>
      </div>
    </div>
  );
}

function ActionButton({ icon, label, desc, onClick, color }) {
  return (
    <button
      onClick={onClick}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        background: "#fff",
        border: "none",
        borderRadius: 14,
        padding: "14px 16px",
        width: "100%",
        cursor: "pointer",
        textAlign: "left",
        transition: "transform 0.1s",
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      }}
      onMouseDown={(e) => (e.currentTarget.style.transform = "scale(0.98)")}
      onMouseUp={(e) => (e.currentTarget.style.transform = "scale(1)")}
    >
      <div
        style={{
          width: 44,
          height: 44,
          borderRadius: 12,
          background: color || "#E3F2FD",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          flexShrink: 0,
        }}
      >
        {icon}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, fontSize: 15, color: "#1a1a2e" }}>
          {label}
        </div>
        <div style={{ fontSize: 12, color: "#888", marginTop: 2 }}>
          {desc}
        </div>
      </div>
      <div style={{ color: "#ccc", fontSize: 18 }}>&#8250;</div>
    </button>
  );
}

// ====== SCREENS ======

function OnboardingScreen({ onComplete }) {
  const [step, setStep] = useState(0);
  const [petType, setPetType] = useState(null);
  const [petName, setPetName] = useState("");

  // Step 0: Welcome
  if (step === 0) {
    return (
      <div style={{ padding: 20, display: "flex", flexDirection: "column", alignItems: "center", minHeight: "100%", background: "#fff" }}>
        <div style={{ fontSize: 64, marginTop: 40, marginBottom: 16 }}>🐾</div>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: "#1a1a2e", textAlign: "center", margin: "0 0 8px" }}>
          Добро пожаловать в VetAI
        </h2>
        <p style={{ fontSize: 14, color: "#888", textAlign: "center", lineHeight: 1.5, margin: "0 0 32px", maxWidth: 280 }}>
          AI-ветеринар в кармане. Загрузите фото, анализы или опишите симптомы — получите оценку за секунды.
        </p>
        <button
          onClick={() => setStep(1)}
          style={{
            width: "100%",
            maxWidth: 300,
            background: "#2AABEE",
            color: "#fff",
            border: "none",
            borderRadius: 12,
            padding: "14px",
            fontSize: 16,
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Начать — это бесплатно
        </button>
        <div style={{ fontSize: 12, color: "#bbb", marginTop: 12, textAlign: "center" }}>
          3 проверки в месяц бесплатно
        </div>
      </div>
    );
  }

  // Step 1: Choose pet type
  if (step === 1) {
    return (
      <div style={{ padding: 20, background: "#fff", minHeight: "100%" }}>
        <div style={{ fontSize: 13, color: "#2AABEE", fontWeight: 600, marginBottom: 4 }}>Шаг 1 из 3</div>
        <h3 style={{ fontSize: 18, fontWeight: 700, color: "#1a1a2e", margin: "0 0 20px" }}>Кто ваш питомец?</h3>
        <div style={{ display: "flex", gap: 12, marginBottom: 20 }}>
          {[
            { type: "cat", icon: "🐱", label: "Кошка" },
            { type: "dog", icon: "🐶", label: "Собака" },
          ].map((p) => (
            <button
              key={p.type}
              onClick={() => setPetType(p.type)}
              style={{
                flex: 1,
                padding: "20px 10px",
                borderRadius: 16,
                border: petType === p.type ? "2px solid #2AABEE" : "2px solid #e0e0e0",
                background: petType === p.type ? "#E3F2FD" : "#fff",
                cursor: "pointer",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 8,
                transition: "all 0.15s",
              }}
            >
              <span style={{ fontSize: 36 }}>{p.icon}</span>
              <span style={{ fontSize: 14, fontWeight: 600, color: "#1a1a2e" }}>{p.label}</span>
            </button>
          ))}
        </div>
        <button
          onClick={() => { if (petType) setStep(2); }}
          style={{
            width: "100%",
            background: petType ? "#2AABEE" : "#e0e0e0",
            color: petType ? "#fff" : "#999",
            border: "none",
            borderRadius: 12,
            padding: "14px",
            fontSize: 15,
            fontWeight: 600,
            cursor: petType ? "pointer" : "default",
          }}
        >
          Далее
        </button>
      </div>
    );
  }  // Step 2: Pet name + basic info
  if (step === 2) {
    return (
      <div style={{ padding: 20, background: "#fff", minHeight: "100%" }}>
        <div style={{ fontSize: 13, color: "#2AABEE", fontWeight: 600, marginBottom: 4 }}>Шаг 2 из 3</div>
        <h3 style={{ fontSize: 18, fontWeight: 700, color: "#1a1a2e", margin: "0 0 20px" }}>Расскажите о питомце</h3>

        <label style={{ fontSize: 13, fontWeight: 600, color: "#555", display: "block", marginBottom: 6 }}>Кличка</label>
        <input
          type="text"
          value={petName}
          onChange={(e) => setPetName(e.target.value)}
          placeholder={petType === "cat" ? "Например, Мурка" : "Например, Рекс"}
          style={{
            width: "100%",
            border: "1.5px solid #e0e0e0",
            borderRadius: 10,
            padding: "12px 14px",
            fontSize: 15,
            outline: "none",
            marginBottom: 16,
            boxSizing: "border-box",
          }}
        />

        <label style={{ fontSize: 13, fontWeight: 600, color: "#555", display: "block", marginBottom: 6 }}>Порода</label>
        <select style={{ width: "100%", border: "1.5px solid #e0e0e0", borderRadius: 10, padding: "12px 14px", fontSize: 15, marginBottom: 16, background: "#fff", boxSizing: "border-box" }}>
          <option>{petType === "cat" ? "Британская" : "Немецкая овчарка"}</option>
          <option>Метис</option>
          <option>Другая</option>
        </select>

        <div style={{ display: "flex", gap: 12, marginBottom: 20 }}>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: "#555", display: "block", marginBottom: 6 }}>Возраст</label>
            <select style={{ width: "100%", border: "1.5px solid #e0e0e0", borderRadius: 10, padding: "12px 14px", fontSize: 15, background: "#fff", boxSizing: "border-box" }}>
              <option>1 год</option><option>2 года</option><option>3 года</option><option>5 лет</option><option>7+</option>
            </select>
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: "#555", display: "block", marginBottom: 6 }}>Вес (кг)</label>
            <input type="number" defaultValue="4" style={{ width: "100%", border: "1.5px solid #e0e0e0", borderRadius: 10, padding: "12px 14px", fontSize: 15, boxSizing: "border-box" }} />
          </div>
        </div>

        <button
          onClick={() => setStep(3)}
          style={{
            width: "100%",
            background: "#2AABEE",
            color: "#fff",
            border: "none",
            borderRadius: 12,
            padding: "14px",
            fontSize: 15,
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Далее
        </button>
      </div>
    );
  }

  // Step 3: Pricing
  return (
    <div style={{ padding: 20, background: "#fff", minHeight: "100%" }}>
      <div style={{ fontSize: 13, color: "#2AABEE", fontWeight: 600, marginBottom: 4 }}>Шаг 3 из 3</div>
      <h3 style={{ fontSize: 18, fontWeight: 700, color: "#1a1a2e", margin: "0 0 6px" }}>Выберите тариф</h3>
      <p style={{ fontSize: 13, color: "#888", margin: "0 0 16px" }}>Начните бесплатно — обновите когда будете готовы</p>

      {[
        { name: "Бесплатный", price: "0 ₽", desc: "3 проверки в месяц", features: ["Фото-диагностика", "Чат с AI", "Базовая история"], color: "#f5f5f5", textColor: "#333", selected: false },
        { name: "Месячный", price: "99 ₽/мес", desc: "Безлимит + все функции", features: ["Безлимитные проверки", "Загрузка анализов", "Полная история", "Напоминания"], color: "#2AABEE", textColor: "#fff", selected: true, badge: "Популярный" },
        { name: "Годовой", price: "1 000 ₽/год", desc: "Экономия 16%", features: ["Всё из месячного", "= 83 ₽/мес", "Приоритетная поддержка"], color: "#f5f5f5", textColor: "#333", selected: false, badge: "-16%" },
      ].map((plan, i) => (
        <div
          key={i}
          style={{
            border: plan.selected ? "2px solid #2AABEE" : "1.5px solid #e0e0e0",
            borderRadius: 14,
            padding: "14px 16px",
            marginBottom: 10,
            background: plan.selected ? "#E3F2FD" : "#fff",
            position: "relative",
            cursor: "pointer",
          }}
        >
          {plan.badge && (
            <div style={{
              position: "absolute", top: -8, right: 12,
              background: plan.selected ? "#2AABEE" : "#4CAF50",
              color: "#fff", fontSize: 10, fontWeight: 700,
              padding: "2px 8px", borderRadius: 6,
            }}>{plan.badge}</div>
          )}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
            <span style={{ fontSize: 15, fontWeight: 700, color: "#1a1a2e" }}>{plan.name}</span>
            <span style={{ fontSize: 15, fontWeight: 700, color: "#2AABEE" }}>{plan.price}</span>
          </div>
          <div style={{ fontSize: 12, color: "#888" }}>{plan.desc}</div>
        </div>
      ))}

      <button
        onClick={() => onComplete(petName || (petType === "cat" ? "Мурка" : "Рекс"))}
        style={{
          width: "100%",
          background: "#2AABEE",
          color: "#fff",
          border: "none",
          borderRadius: 12,
          padding: "14px",
          fontSize: 15,
          fontWeight: 600,
          cursor: "pointer",
          marginTop: 6,
        }}
      >
        Начать бесплатно
      </button>
      <div style={{ fontSize: 11, color: "#bbb", textAlign: "center", marginTop: 8 }}>
        Подписку можно оформить в любой момент
      </div>
    </div>
  );
}
function HomeScreen({ onNavigate, petName }) {
  return (
    <div style={{ padding: 12, display: "flex", flexDirection: "column", gap: 8 }}>
      {/* Pet card */}
      <div
        style={{
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          borderRadius: 16,
          padding: 18,
          color: "#fff",
          display: "flex",
          alignItems: "center",
          gap: 14,
        }}
      >
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: 28,
            background: "rgba(255,255,255,0.2)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 30,
          }}
        >
          🐱
        </div>
        <div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>
            {petName || "Мурка"}
          </div>
          <div style={{ fontSize: 13, opacity: 0.85 }}>
            Кошка · 3 года · Британская
          </div>
          <div
            style={{
              fontSize: 12,
              opacity: 0.7,
              marginTop: 4,
              display: "flex",
              alignItems: "center",
              gap: 4,
            }}
          >
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: 4,
                background: "#4ade80",
                display: "inline-block",
              }}
            />
            Последний осмотр: 15 марта
          </div>
        </div>
      </div>

      {/* Quick actions */}
      <div
        style={{
          fontSize: 13,
          fontWeight: 600,
          color: "#666",
          padding: "8px 4px 2px",
          textTransform: "uppercase",
          letterSpacing: 0.5,
        }}
      >
        Что беспокоит?
      </div>

      <ActionButton
        icon="📸"
        label="Загрузить фото"
        desc="Кожа, глаза, раны, опухоли"
        onClick={() => onNavigate(screens.UPLOAD_PHOTO)}
        color="#FFF3E0"
      />
      <ActionButton
        icon="📋"
        label="Загрузить анализы"
        desc="PDF, фото результатов из лаборатории"
        onClick={() => onNavigate(screens.UPLOAD_ANALYSIS)}
        color="#E8F5E9"
      />
      <ActionButton
        icon="💬"
        label="Описать симптомы"
        desc="AI-чат задаст уточняющие вопросы"
        onClick={() => onNavigate(screens.SYMPTOM_CHAT)}
        color="#E3F2FD"
      />
      <ActionButton
        icon="📖"
        label="История проверок"
        desc="3 записи за последний месяц"
        onClick={() => onNavigate(screens.HISTORY)}
        color="#F3E5F5"
      />

      {/* Bottom promo */}
      <div
        style={{
          background: "#fff",
          borderRadius: 14,
          padding: "12px 16px",
          display: "flex",
          alignItems: "center",
          gap: 10,
          marginTop: 4,
        }}
      >
        <span style={{ fontSize: 28 }}>🏥</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "#1a1a2e" }}>
            Ветклиники рядом
          </div>
          <div style={{ fontSize: 12, color: "#888" }}>
            Запись к ветеринару в 1 клик
          </div>
        </div>
        <div
          style={{
            background: "#2AABEE",
            color: "#fff",
            borderRadius: 8,
            padding: "6px 12px",
            fontSize: 12,
            fontWeight: 600,
          }}
        >
          3 рядом
        </div>
      </div>
    </div>
  );
}

function UploadPhotoScreen({ onNavigate }) {
  const [step, setStep] = useState(0);

  if (step === 0) {
    return (
      <div style={{ padding: 12 }}>
        <ChatBubble from="bot" time="9:42">
          <strong>Загрузите фото питомца</strong>
          <br />
          Для точной оценки сфотографируйте проблемную область при хорошем
          освещении. Можно загрузить до 5 фото.
        </ChatBubble>

        <div
          style={{
            margin: "12px",
            border: "2px dashed #2AABEE",
            borderRadius: 16,
            background: "#fff",
            padding: 28,
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: 44, marginBottom: 8 }}>📷</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "#1a1a2e" }}>
            Нажмите для загрузки
          </div>
          <div style={{ fontSize: 12, color: "#999", marginTop: 4 }}>
            Камера или галерея
          </div>
          <div
            style={{
              display: "flex",
              gap: 8,
              justifyContent: "center",
              marginTop: 14,
            }}
          >
            <button
              onClick={() => setStep(1)}
              style={{
                background: "#2AABEE",
                color: "#fff",
                border: "none",
                borderRadius: 10,
                padding: "10px 20px",
                fontSize: 14,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              📷 Камера
            </button>
            <button
              onClick={() => setStep(1)}
              style={{
                background: "#f0f0f0",
                color: "#333",
                border: "none",
                borderRadius: 10,
                padding: "10px 20px",
                fontSize: 14,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              🖼 Галерея
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (step === 1) {
    return (
      <div style={{ padding: 12 }}>
        <ChatBubble from="bot" time="9:42">
          Загрузите фото проблемной области
        </ChatBubble>

        {/* Simulated uploaded photo */}
        <div style={{ display: "flex", justifyContent: "flex-end", padding: "2px 12px" }}>
          <div
            style={{
              background: "#EFFDDE",
              borderRadius: "18px 4px 18px 18px",
              padding: 6,
              maxWidth: "70%",
            }}
          >
            <div
              style={{
                width: "100%",
                height: 140,
                borderRadius: 12,
                background: "linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 50,
              }}
            >
              🐱
            </div>
            <div style={{ fontSize: 11, color: "#999", textAlign: "right", padding: "4px 4px 0" }}>
              photo_1.jpg · 9:43
            </div>
          </div>
        </div>

        <ChatBubble from="bot" time="9:43">
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
            <div
              className="pulse-dot"
              style={{
                width: 8,
                height: 8,
                borderRadius: 4,
                background: "#2AABEE",
                animation: "pulse 1.5s infinite",
              }}
            />
            <span style={{ fontSize: 13, color: "#2AABEE", fontWeight: 600 }}>
              Анализирую изображение...
            </span>
          </div>
        </ChatBubble>

        <div style={{ padding: "8px 12px" }}>
          <button
            onClick={() => setStep(2)}
            style={{
              width: "100%",
              background: "#2AABEE",
              color: "#fff",
              border: "none",
              borderRadius: 12,
              padding: "12px",
              fontSize: 14,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Смотреть результат →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: 12 }}>
      <ChatBubble from="bot" time="9:43">
        Загрузите фото
      </ChatBubble>
      <div style={{ display: "flex", justifyContent: "flex-end", padding: "2px 12px" }}>
        <div
          style={{
            background: "#EFFDDE",
            borderRadius: "18px 4px 18px 18px",
            padding: 6,
            maxWidth: "70%",
          }}
        >
          <div
            style={{
              width: "100%",
              height: 100,
              borderRadius: 12,
              background: "linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 40,
            }}
          >
            🐱
          </div>
        </div>
      </div>

      <ChatBubble from="bot" time="9:44">
        <div style={{ marginBottom: 8 }}>
          <strong>Результат AI-анализа:</strong>
        </div>
        <div
          style={{
            background: "#FFF3E0",
            borderRadius: 10,
            padding: "10px 12px",
            marginBottom: 8,
            border: "1px solid #FFE0B2",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
            <span style={{ fontSize: 16 }}>⚠️</span>
            <strong style={{ color: "#E65100" }}>Средний приоритет</strong>
          </div>
          <div style={{ fontSize: 13 }}>
            <strong>Вероятный диагноз:</strong> Аллергический дерматит
            <br />
            <strong>Уверенность:</strong> 78%
          </div>
        </div>
        <div style={{ fontSize: 13, lineHeight: 1.5 }}>
          Покраснение и шелушение в области за ушами характерно для аллергической
          реакции. Возможные причины: смена корма, бытовая химия, сезонная
          аллергия.
        </div>
      </ChatBubble>

      <ChatBubble from="bot" time="9:44">
        <strong>Рекомендации:</strong>
        <div style={{ fontSize: 13, marginTop: 4, lineHeight: 1.5 }}>
          1. Исключите новые продукты из рациона
          <br />
          2. Визит к ветеринару в течение 48 часов
          <br />
          3. Не обрабатывайте область спиртосодержащими средствами
        </div>
        <div style={{ marginTop: 8, display: "flex", gap: 6, flexWrap: "wrap" }}>
          <button
            onClick={() => onNavigate(screens.HOME)}
            style={{
              background: "#2AABEE",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              padding: "8px 14px",
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            🏥 Найти ветклинику
          </button>
          <button
            style={{
              background: "#f0f0f0",
              color: "#333",
              border: "none",
              borderRadius: 8,
              padding: "8px 14px",
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            💬 Задать вопрос
          </button>
        </div>
      </ChatBubble>

      <div
        style={{
          margin: "8px 12px",
          background: "#fff",
          borderRadius: 10,
          padding: "10px 14px",
          fontSize: 11,
          color: "#999",
          textAlign: "center",
          lineHeight: 1.4,
        }}
      >
        ⚕️ Это предварительная AI-оценка, не заменяющая консультацию
        ветеринарного врача
      </div>
    </div>
  );
}
function UploadAnalysisScreen({ onNavigate }) {
  const [step, setStep] = useState(0);

  if (step === 0) {
    return (
      <div style={{ padding: 12 }}>
        <ChatBubble from="bot" time="9:45">
          <strong>Загрузите результаты анализов</strong>
          <br />
          Поддерживаются: PDF-файлы, фото бланков, скриншоты из лабораторий.
          AI расшифрует значения и укажет отклонения.
        </ChatBubble>

        <div
          style={{
            margin: "12px",
            background: "#fff",
            borderRadius: 16,
            padding: 18,
          }}
        >
          <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 12, color: "#1a1a2e" }}>
            Что можно загрузить:
          </div>
          {[
            { icon: "🩸", label: "Общий анализ крови" },
            { icon: "🧪", label: "Биохимический анализ" },
            { icon: "🔬", label: "Анализ мочи / кала" },
            { icon: "📄", label: "Результаты УЗИ / рентген" },
            { icon: "💉", label: "Паспорт вакцинации" },
          ].map((item, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "8px 0",
                borderBottom: i < 4 ? "1px solid #f0f0f0" : "none",
                fontSize: 14,
              }}
            >
              <span style={{ fontSize: 20 }}>{item.icon}</span>
              {item.label}
            </div>
          ))}
          <button
            onClick={() => setStep(1)}
            style={{
              width: "100%",
              background: "#2AABEE",
              color: "#fff",
              border: "none",
              borderRadius: 12,
              padding: "12px",
              fontSize: 14,
              fontWeight: 600,
              cursor: "pointer",
              marginTop: 14,
            }}
          >
            📎 Загрузить файл
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: 12 }}>
      <ChatBubble from="bot" time="9:45">
        Загрузите результаты анализов
      </ChatBubble>

      {/* Simulated uploaded file */}
      <div style={{ display: "flex", justifyContent: "flex-end", padding: "2px 12px" }}>
        <div
          style={{
            background: "#EFFDDE",
            borderRadius: "18px 4px 18px 18px",
            padding: "10px 14px",
            maxWidth: "75%",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div
              style={{
                width: 40,
                height: 48,
                background: "#ef5350",
                borderRadius: 6,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#fff",
                fontSize: 11,
                fontWeight: 700,
              }}
            >
              PDF
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600 }}>
                analiz_krovi_murka.pdf
              </div>
              <div style={{ fontSize: 11, color: "#999" }}>245 KB</div>
            </div>
          </div>
          <div style={{ fontSize: 11, color: "#999", textAlign: "right", marginTop: 4 }}>
            9:46
          </div>
        </div>
      </div>

      <ChatBubble from="bot" time="9:46">
        <div style={{ marginBottom: 8 }}>
          <strong>Расшифровка анализа крови:</strong>
        </div>

        <div style={{ fontSize: 13 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "4px 0",
              borderBottom: "1px solid #f0f0f0",
            }}
          >
            <span>Гемоглобин</span>
            <span style={{ color: "#4caf50", fontWeight: 600 }}>
              128 г/л ✓
            </span>
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "4px 0",
              borderBottom: "1px solid #f0f0f0",
            }}
          >
            <span>Лейкоциты</span>
            <span style={{ color: "#f44336", fontWeight: 600 }}>
              18.5 ↑
            </span>
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "4px 0",
              borderBottom: "1px solid #f0f0f0",
            }}
          >
            <span>Тромбоциты</span>
            <span style={{ color: "#4caf50", fontWeight: 600 }}>
              310 ✓
            </span>
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "4px 0",
            }}
          >
            <span>АЛТ</span>
            <span style={{ color: "#ff9800", fontWeight: 600 }}>
              85 ↑
            </span>
          </div>
        </div>

        <div
          style={{
            background: "#FFF3E0",
            borderRadius: 8,
            padding: "8px 10px",
            marginTop: 10,
            fontSize: 13,
            border: "1px solid #FFE0B2",
          }}
        >
          ⚠️ <strong>Лейкоциты повышены</strong> — возможен воспалительный
          процесс. <strong>АЛТ незначительно повышен</strong> — рекомендуется
          контроль через 2 недели.
        </div>

        <div style={{ marginTop: 8, display: "flex", gap: 6 }}>
          <button
            onClick={() => onNavigate(screens.HOME)}
            style={{
              background: "#2AABEE",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              padding: "8px 12px",
              fontSize: 12,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            📊 Полный отчёт
          </button>
          <button
            style={{
              background: "#f0f0f0",
              color: "#333",
              border: "none",
              borderRadius: 8,
              padding: "8px 12px",
              fontSize: 12,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            🏥 К ветеринару
          </button>
        </div>
      </ChatBubble>

      <div
        style={{
          margin: "8px 12px",
          background: "#fff",
          borderRadius: 10,
          padding: "10px 14px",
          fontSize: 11,
          color: "#999",
          textAlign: "center",
        }}
      >
        ⚕️ Предварительная AI-расшифровка. Окончательную интерпретацию даёт
        ветврач.
      </div>
    </div>
  );
}

function SymptomChatScreen() {
  const [messages, setMessages] = useState([
    {
      from: "bot",
      text: "Опишите, что беспокоит вашего питомца. Я задам уточняющие вопросы для предварительной оценки.",
      time: "9:47",
    },
  ]);
  const [input, setInput] = useState("");
  const [questionIndex, setQuestionIndex] = useState(0);

  const botQuestions = [
    {
      trigger: true,
      response:
        "Понял, кошка часто чешется. Несколько уточняющих вопросов:\n\n1. Как давно началось?\n2. Есть ли выпадение шерсти?\n3. Меняли ли корм в последнее время?",
    },
    {
      trigger: true,
      response:
        'Спасибо за подробности. На основе описания:\n\n🔍 Наиболее вероятно: **пищевая аллергия** или **блошиный дерматит**.\n\nРекомендую загрузить фото проблемных участков для более точной оценки. Нажмите "📸 Загрузить фото" ниже.',
    },
  ];

  const handleSend = () => {
    if (!input.trim()) return;
    const newMessages = [
      ...messages,
      { from: "user", text: input, time: "9:48" },
    ];

    if (questionIndex < botQuestions.length) {
      newMessages.push({
        from: "bot",
        text: botQuestions[questionIndex].response,
        time: "9:48",
      });
      setQuestionIndex(questionIndex + 1);
    }

    setMessages(newMessages);
    setInput("");
  };

  return (
    <div
      style={{ display: "flex", flexDirection: "column", height: "100%" }}
    >
      <div style={{ flex: 1, padding: "8px 0", overflow: "auto" }}>
        {messages.map((msg, i) => (
          <ChatBubble key={i} from={msg.from} time={msg.time}>
            <span style={{ whiteSpace: "pre-line" }}>{msg.text}</span>
          </ChatBubble>
        ))}
      </div>
      {/* Input bar */}
      <div
        style={{
          background: "#fff",
          padding: "8px 12px",
          display: "flex",
          gap: 8,
          alignItems: "center",
          borderTop: "1px solid #e0e0e0",
        }}
      >
        <button
          style={{
            background: "none",
            border: "none",
            fontSize: 22,
            cursor: "pointer",
            padding: 4,
          }}
        >
          📎
        </button>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Опишите симптомы..."
          style={{
            flex: 1,
            border: "1px solid #e0e0e0",
            borderRadius: 20,
            padding: "8px 14px",
            fontSize: 14,
            outline: "none",
          }}
        />
        <button
          onClick={handleSend}
          style={{
            background: "#2AABEE",
            border: "none",
            borderRadius: "50%",
            width: 36,
            height: 36,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            color: "#fff",
            fontSize: 16,
          }}
        >
          ▶
        </button>
      </div>
    </div>
  );
}

function HistoryScreen() {
  const records = [
    {
      date: "25 марта",
      type: "📸 Фото",
      result: "Аллергический дерматит",
      severity: "medium",
    },
    {
      date: "20 марта",
      type: "📋 Анализ крови",
      result: "Лейкоциты ↑, АЛТ ↑",
      severity: "medium",
    },
    {
      date: "5 марта",
      type: "💬 Чат-консультация",
      result: "Смена корма — норма",
      severity: "low",
    },
  ];

  const severityColors = {
    low: { bg: "#E8F5E9", color: "#2E7D32", label: "Норма" },
    medium: { bg: "#FFF3E0", color: "#E65100", label: "Внимание" },
    high: { bg: "#FFEBEE", color: "#C62828", label: "Срочно" },
  };

  return (
    <div style={{ padding: 12 }}>
      <div
        style={{
          fontSize: 13,
          fontWeight: 600,
          color: "#666",
          padding: "4px 4px 8px",
          textTransform: "uppercase",
          letterSpacing: 0.5,
        }}
      >
        Март 2026
      </div>
      {records.map((rec, i) => {
        const sev = severityColors[rec.severity];
        return (
          <div
            key={i}
            style={{
              background: "#fff",
              borderRadius: 12,
              padding: "12px 14px",
              marginBottom: 8,
              display: "flex",
              alignItems: "center",
              gap: 12,
            }}
          >
            <div style={{ flex: 1 }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  marginBottom: 4,
                }}
              >
                <span style={{ fontSize: 14 }}>{rec.type}</span>
                <span style={{ fontSize: 12, color: "#999" }}>
                  {rec.date}
                </span>
              </div>
              <div style={{ fontSize: 14, fontWeight: 500 }}>{rec.result}</div>
            </div>
            <div
              style={{
                background: sev.bg,
                color: sev.color,
                borderRadius: 6,
                padding: "4px 10px",
                fontSize: 11,
                fontWeight: 600,
              }}
            >
              {sev.label}
            </div>
          </div>
        );
      })}

      <div
        style={{
          background: "#fff",
          borderRadius: 12,
          padding: "14px",
          marginTop: 8,
          textAlign: "center",
        }}
      >
        <div style={{ fontSize: 13, color: "#888" }}>
          Безлимитные проверки + полная история
        </div>
        <div style={{ display: "flex", gap: 8, marginTop: 10, justifyContent: "center" }}>
          <button
            style={{
              background: "linear-gradient(135deg, #667eea, #764ba2)",
              color: "#fff",
              border: "none",
              borderRadius: 10,
              padding: "10px 18px",
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            99 ₽/мес
          </button>
          <button
            style={{
              background: "#4CAF50",
              color: "#fff",
              border: "none",
              borderRadius: 10,
              padding: "10px 18px",
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            1 000 ₽/год (-16%)
          </button>
        </div>
      </div>
    </div>
  );
}
// ====== MAIN APP ======

export default function VetAITelegramConcept() {
  const [screen, setScreen] = useState(screens.ONBOARDING);
  const [activeDemo, setActiveDemo] = useState("app");
  const [petName, setPetName] = useState("");

  const screenTitles = {
    [screens.ONBOARDING]: "VetAI",
    [screens.HOME]: "VetAI",
    [screens.UPLOAD_PHOTO]: "Фото-диагностика",
    [screens.UPLOAD_ANALYSIS]: "Анализы",
    [screens.SYMPTOM_CHAT]: "Чат с AI",
    [screens.HISTORY]: "История",
  };

  const handleOnboardingComplete = (name) => {
    setPetName(name);
    setScreen(screens.HOME);
  };

  const renderScreen = () => {
    switch (screen) {
      case screens.ONBOARDING:
        return <OnboardingScreen onComplete={handleOnboardingComplete} />;
      case screens.HOME:
        return <HomeScreen onNavigate={setScreen} petName={petName} />;
      case screens.UPLOAD_PHOTO:
        return <UploadPhotoScreen onNavigate={setScreen} />;
      case screens.UPLOAD_ANALYSIS:
        return <UploadAnalysisScreen onNavigate={setScreen} />;
      case screens.SYMPTOM_CHAT:
        return <SymptomChatScreen />;
      case screens.HISTORY:
        return <HistoryScreen />;
      default:
        return <HomeScreen onNavigate={setScreen} petName={petName} />;
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #0f0c29, #302b63, #24243e)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "24px 16px",
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      }}
    >
      <h1
        style={{
          color: "#fff",
          fontSize: 22,
          fontWeight: 700,
          marginBottom: 4,
          textAlign: "center",
        }}
      >
        VetAI — Telegram Mini App
      </h1>
      <p
        style={{
          color: "rgba(255,255,255,0.6)",
          fontSize: 14,
          marginBottom: 20,
          textAlign: "center",
        }}
      >
        Интерактивный прототип пользовательского сценария
      </p>

      {/* Demo switcher */}
      <div
        style={{
          display: "flex",
          gap: 8,
          marginBottom: 20,
          flexWrap: "wrap",
          justifyContent: "center",
        }}
      >
        {[
          { id: "app", label: "📱 Mini App" },
          { id: "flow", label: "🔄 User Flow" },
          { id: "finance", label: "💰 Финмодель" },
          { id: "marketing", label: "📣 Маркетинг" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveDemo(tab.id)}
            style={{
              background:
                activeDemo === tab.id
                  ? "rgba(42,171,238,0.9)"
                  : "rgba(255,255,255,0.1)",
              color: "#fff",
              border: "none",
              borderRadius: 10,
              padding: "8px 18px",
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeDemo === "app" && (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
          <PhoneFrame
            title={screenTitles[screen]}
            onBack={screen !== screens.HOME ? () => setScreen(screens.HOME) : null}
          >
            {renderScreen()}
          </PhoneFrame>

          {/* Screen navigation hints */}
          <div
            style={{
              display: "flex",
              gap: 6,
              flexWrap: "wrap",
              justifyContent: "center",
              maxWidth: 400,
            }}
          >
            {Object.entries({
              [screens.ONBOARDING]: "👋 Регистрация",
              [screens.HOME]: "🏠 Главная",
              [screens.UPLOAD_PHOTO]: "📸 Фото",
              [screens.UPLOAD_ANALYSIS]: "📋 Анализы",
              [screens.SYMPTOM_CHAT]: "💬 Чат",
              [screens.HISTORY]: "📖 История",
            }).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setScreen(key)}
                style={{
                  background:
                    screen === key
                      ? "rgba(42,171,238,0.8)"
                      : "rgba(255,255,255,0.1)",
                  color: "#fff",
                  border: "none",
                  borderRadius: 8,
                  padding: "6px 12px",
                  fontSize: 12,
                  cursor: "pointer",
                }}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      )}

      {activeDemo === "flow" && (
        <div
          style={{
            background: "rgba(255,255,255,0.06)",
            borderRadius: 20,
            padding: 28,
            maxWidth: 700,
            width: "100%",
            color: "#fff",
          }}
        >
          <h2
            style={{
              fontSize: 18,
              fontWeight: 700,
              marginBottom: 20,
              textAlign: "center",
            }}
          >
            Пользовательский сценарий Фазы 1
          </h2>

          {[
            {
              step: "1",
              title: "Вход через Telegram",
              desc: 'Пользователь находит бота @VetAI_bot или Mini App через поиск / ссылку / QR в ветклинике. Нажимает "Запустить".',
              color: "#2AABEE",
            },
            {
              step: "2",
              title: "Регистрация питомца (30 сек)",
              desc: "Имя, вид (кошка/собака), порода, возраст, вес. Данные сохраняются для персонализации диагностики.",
              color: "#9C27B0",
            },
            {
              step: "3",
              title: "Выбор действия",
              desc: '📸 Загрузить фото проблемы\n📋 Загрузить результаты анализов (PDF / фото бланка)\n💬 Описать симптомы в чате\n📖 Посмотреть историю',
              color: "#FF9800",
            },
            {
              step: "4a",
              title: "Сценарий «Фото»",
              desc: "Фото кожи/глаз/ран → CV-модель классифицирует → выдаёт предварительный диагноз с % уверенности → рекомендации → кнопка «Найти ветклинику»",
              color: "#4CAF50",
            },
            {
              step: "4b",
              title: "Сценарий «Анализы»",
              desc: "PDF или фото бланка → OCR извлекает значения → сравнение с нормами для данного вида/породы/возраста → подсвечивает отклонения → расшифровка простым языком",
              color: "#4CAF50",
            },
            {
              step: "4c",
              title: "Сценарий «Чат»",
              desc: "LLM задаёт структурированные вопросы (когда началось? что ел? есть ли температура?) → собирает анамнез → предварительная оценка → просит фото при необходимости",
              color: "#4CAF50",
            },
            {
              step: "5",
              title: "Результат + CTA",
              desc: "Диагноз (предварительный) + уровень срочности (зелёный/жёлтый/красный) + рекомендации + кнопка записи в ветклинику + сохранение в историю",
              color: "#E91E63",
            },
            {
              step: "6",
              title: "Монетизация",
              desc: "Бесплатно: 3 проверки/мес. Подписка 99₽/мес или 1 000₽/год: безлимит + история + анализы + напоминания. Лидогенерация: клик → запись в клинику = 200-500₽ комиссия",
              color: "#795548",
            },
          ].map((item, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                gap: 14,
                marginBottom: 16,
                alignItems: "flex-start",
              }}
            >
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 18,
                  background: item.color,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 14,
                  fontWeight: 700,
                  flexShrink: 0,
                }}
              >
                {item.step}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 4 }}>
                  {item.title}
                </div>
                <div
                  style={{
                    fontSize: 13,
                    color: "rgba(255,255,255,0.7)",
                    lineHeight: 1.5,
                    whiteSpace: "pre-line",
                  }}
                >
                  {item.desc}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeDemo === "finance" && (
        <div
          style={{
            background: "rgba(255,255,255,0.06)",
            borderRadius: 20,
            padding: 28,
            maxWidth: 750,
            width: "100%",
            color: "#fff",
          }}
        >
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 6, textAlign: "center" }}>
            Финансовая модель VetAI
          </h2>
          <p style={{ fontSize: 13, color: "rgba(255,255,255,0.5)", textAlign: "center", marginBottom: 20 }}>
            Интерактивный прототип — откройте в React для полной функциональности
          </p>
          <div style={{ fontSize: 13, lineHeight: 1.8, color: "rgba(255,255,255,0.8)" }}>
            <strong>MVP инвестиции:</strong> ~400k ₽<br/>
            <strong>Целевая аудитория (TAM):</strong> 18.7 млн владельцев животных в TG<br/>
            <strong>SOM год 1:</strong> 6,000 пользователей<br/>
            <strong>Прогноз выручки год 1:</strong> 3–5 млн ₽<br/>
            <strong>Прогноз выручки год 2:</strong> 20–45 млн ₽<br/>
            <strong>Маржа:</strong> 50–70%<br/>
          </div>
        </div>
      )}

      {activeDemo === "marketing" && (
        <div
          style={{
            background: "rgba(255,255,255,0.06)",
            borderRadius: 20,
            padding: 28,
            maxWidth: 700,
            width: "100%",
            color: "#fff",
          }}
        >
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 20, textAlign: "center" }}>
            Маркетинговая стратегия
          </h2>

          {[
            {
              phase: "Pre-launch",
              budget: "50k ₽",
              tactics: ["Тизеры в pet-каналах (10–15)", "QR в ветклиниках (5–10)", "Контент в своём канале"],
              result: "1–2k подписчиков на waitlist",
            },
            {
              phase: "Launch (месяц 1–2)",
              budget: "155k ₽",
              tactics: ["Telegram Ads (30k/мес)", "Микроинфлюенсеры (20k/мес)", "Виральная механика"],
              result: "3–8k пользователей, CPA 25–50₽",
            },
            {
              phase: "Рост (месяц 3–6)",
              budget: "Органический",
              tactics: ["Геймификация (паспорт здоровья)", "B2B партнёрства (корма, магазины)", "PR (vc.ru/Habr)"],
              result: "Retention +30–40%, +15k пользователей",
            },
          ].map((item, i) => (
            <div
              key={i}
              style={{
                background: "rgba(255,255,255,0.04)",
                borderRadius: 12,
                padding: "16px",
                marginBottom: 12,
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                <div style={{ fontSize: 14, fontWeight: 700 }}>{item.phase}</div>
                <div style={{ fontSize: 12, color: "#FFD54F" }}>{item.budget}</div>
              </div>
              <div style={{ fontSize: 13, lineHeight: 1.8 }}>
                <strong>Тактика:</strong> {item.tactics.join(", ")}<br/>
                <strong>Результат:</strong> {item.result}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}