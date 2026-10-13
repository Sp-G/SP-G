import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Background, C, Captions, ease, Logo, Phone, Sfx, useSpring, Voice, wordAt } from "../theme";

/** Closing: price, logo, call to action. */
export const Cta: React.FC = () => {
  const frame = useCurrentFrame();
  const brandAt = wordAt("cta", "Coffee", 70);
  const goAt = wordAt("cta", "подключайся", brandAt + 20);
  const logo = useSpring(brandAt - 2, 9);
  const btn = useSpring(goAt - 2, 10);
  const phoneL = useSpring(6, 16, 1);
  const phoneR = useSpring(12, 16, 1);
  const shimmer = ((frame - goAt) % 50) / 50;
  const pulse = 1 + 0.035 * Math.max(0, Math.sin((frame - goAt) / 5)) * (frame > goAt + 10 ? 1 : 0);
  return (
    <AbsoluteFill>
      <Background glowY={35} />
      <Voice id="cta" />
      <Sfx src="whoosh" at={0} volume={0.35} />
      <Sfx src="impact" at={brandAt - 2} volume={0.45} />
      <Sfx src="success" at={goAt} volume={0.35} />
      <div style={{ opacity: 0.5 }}>
        <Phone src="coins" width={420} x={-50} y={1180 + (1 - phoneL) * 600} rotate={-12} />
        <Phone src="profile" width={420} x={710} y={1180 + (1 - phoneR) * 600} rotate={12} />
      </div>
      <Phone src="home" width={460} y={1110 + (1 - phoneL) * 700} />
      <AbsoluteFill
        style={{ background: "linear-gradient(180deg, rgba(20,15,11,0) 60%, rgba(20,15,11,0.85) 100%)" }}
      />
      <Captions id="cta" top={150} size={80} gold={["1 490", "Coffee"]} />
      <div
        style={{
          position: "absolute",
          top: 590,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          scale: String(2 - logo),
          opacity: Math.min(1, logo * 2),
        }}
      >
        <div style={{ marginRight: 110 }}>
          <Logo size={110} />
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          top: 850,
          left: 140,
          right: 140,
          height: 140,
          borderRadius: 70,
          background: `linear-gradient(100deg, ${C.gold} ${shimmer * 140 - 30}%, ${C.goldLight} ${shimmer * 140 - 10}%, ${C.gold} ${shimmer * 140 + 10}%)`,
          boxShadow: "0 24px 60px rgba(217,167,95,0.45)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "Inter Display",
          fontWeight: 900,
          fontSize: 58,
          color: C.bg,
          scale: String(btn * pulse),
        }}
      >
        coffeepass.kz
      </div>
      <div
        style={{
          position: "absolute",
          top: 1015,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          gap: 16,
          opacity: ease(frame, [goAt + 8, goAt + 18]),
        }}
      >
        {["KZ", "RU", "EN"].map((l) => (
          <div
            key={l}
            style={{
              padding: "8px 22px",
              borderRadius: 100,
              border: `2px solid ${C.cardBorder}`,
              fontFamily: "Inter",
              fontWeight: 800,
              fontSize: 28,
              color: C.muted,
            }}
          >
            {l}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
