import { useNavigate } from "react-router-dom";
import { Home, ArrowLeft, Package } from "lucide-react";

const NotFoundPage = () => {
  const navigate = useNavigate();

  return (
    <div
      className="relative min-h-screen rounded-2xl overflow-hidden flex items-center justify-center"
      style={{
        background:
          "linear-gradient(135deg, #0a1a0d 0%, #0f2318 40%, #071510 100%)",
      }}
    >
      {/* ── Ambient blobs ── */}
      <div
        className="absolute rounded-full blur-3xl opacity-30 pointer-events-none"
        style={{
          width: 500,
          height: 500,
          top: "-10%",
          left: "-10%",
          background: "radial-gradient(circle, #16a34a 0%, transparent 70%)",
        }}
      />
      <div
        className="absolute rounded-full blur-3xl opacity-20 pointer-events-none"
        style={{
          width: 400,
          height: 400,
          bottom: "-5%",
          right: "-5%",
          background: "radial-gradient(circle, #15803d 0%, transparent 70%)",
        }}
      />
      <div
        className="absolute rounded-full blur-2xl opacity-15 pointer-events-none"
        style={{
          width: 250,
          height: 250,
          top: "50%",
          left: "60%",
          transform: "translate(-50%, -50%)",
          background: "radial-gradient(circle, #22c55e 0%, transparent 70%)",
        }}
      />

      {/* ── Grid overlay ── */}
      <div
        className="absolute inset-0 pointer-events-none opacity-5"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.4) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      {/* ── Glass card ── */}
      <div
        className="relative z-10 flex flex-col items-center text-center px-10 py-14 rounded-3xl"
        style={{
          maxWidth: 480,
          width: "90%",
          background: "rgba(255,255,255,0.04)",
          backdropFilter: "blur(24px)",
          WebkitBackdropFilter: "blur(24px)",
          border: "1px solid rgba(255,255,255,0.09)",
          boxShadow:
            "0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.08)",
        }}
      >
        {/* Icon */}
        <div
          className="flex items-center justify-center rounded-2xl mb-7"
          style={{
            width: 72,
            height: 72,
            background: "rgba(22,163,74,0.15)",
            border: "1px solid rgba(22,163,74,0.3)",
            boxShadow: "0 0 32px rgba(22,163,74,0.15)",
          }}
        >
          <Package size={34} className="text-green-400" />
        </div>

        {/* 404 number */}
        <div
          className="font-black leading-none mb-3 select-none"
          style={{
            fontSize: 100,
            background:
              "linear-gradient(135deg, #4ade80 0%, #16a34a 60%, #15803d 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
            letterSpacing: "-4px",
            lineHeight: 1,
          }}
        >
          404
        </div>

        {/* Title */}
        <h1 className="text-white font-bold text-2xl mb-2">Sahifa topilmadi</h1>

        {/* Subtitle */}
        <p
          className="text-gray-400 text-sm leading-relaxed mb-9"
          style={{ maxWidth: 320 }}
        >
          Siz izlayotgan sahifa mavjud emas yoki boshqa manzilga ko'chirilgan.
        </p>

        {/* Divider */}
        <div
          className="w-full mb-8"
          style={{ height: 1, background: "rgba(255,255,255,0.07)" }}
        />

        {/* Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-3 w-full">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center justify-center gap-2 rounded-xl px-5 py-3 text-sm font-semibold w-full sm:w-auto transition-all duration-150 hover:bg-white/10 active:scale-95 cursor-pointer"
            style={{
              background: "rgba(255,255,255,0.06)",
              border: "1px solid rgba(255,255,255,0.1)",
              color: "#d1fae5",
            }}
          >
            <ArrowLeft size={15} />
            Orqaga
          </button>

          <button
            onClick={() => navigate("/")}
            className="flex items-center justify-center gap-2 rounded-xl px-5 py-3 text-sm font-semibold w-full sm:flex-1 transition-all duration-150 active:scale-95 cursor-pointer"
            style={{
              background: "linear-gradient(135deg, #16a34a 0%, #15803d 100%)",
              color: "white",
              boxShadow: "0 4px 16px rgba(22,163,74,0.35)",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.boxShadow =
                "0 4px 24px rgba(22,163,74,0.55)")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.boxShadow =
                "0 4px 16px rgba(22,163,74,0.35)")
            }
          >
            <Home size={15} />
            Bosh sahifaga
          </button>
        </div>
      </div>

      {/* ── Branding footer ── */}
      <div className="absolute bottom-6 left-0 right-0 flex justify-center z-10">
        <span className="text-gray-600 text-xs">
          © 2026 Ko'prikQurilish AJ — E-Ombor
        </span>
      </div>
    </div>
  );
};

export default NotFoundPage;
