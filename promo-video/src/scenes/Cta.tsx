import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Background, C, ease, Headline, Logo, Phone, Sfx, useSpring, Voice } from "../theme";

/** Closing: logo, slogan, call to action. */
export const Cta: React.FC = () => {
  const frame = useCurrentFrame();
  const logo = useSpring(4, 12);
  const btn = useSpring(70, 11);
  const phoneL = useSpring(20, 16, 1);
  const phoneR = useSpring(28, 16, 1);
  const shimmer = ((frame - 80) % 70) / 70;
  return (
    <AbsoluteFill>
      <Background glowY={40} />
      <Voice id="cta" />
      <Sfx src="whoosh" at={0} volume={0.35} />
      <Sfx src="success" at={70} volume={0.3} />
      {/* fanned phones in the background */}
      <div style={{ opacity: 0.55 }}>
        <Phone src="coins" width={440} x={-60} y={1060 + (1 - phoneL) * 600} rotate={-12} />
        <Phone src="profile" width={440} x={700} y={1060 + (1 - phoneR) * 600} rotate={12} />
      </div>
      <Phone src="home" width={480} y={1000 + (1 - phoneL) * 700} />
      <AbsoluteFill
        style={{
          background: "linear-gradient(180deg, rgba(20,15,11,0) 55%, rgba(20,15,11,0.85) 100%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 170,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          scale: String(0.5 + 0.5 * logo),
          opacity: Math.min(1, logo * 1.5),
        }}
      >
        <div style={{ marginRight: 120 }}>
          <Logo size={140} />
        </div>
      </div>
      <Headline text="Больше кофе — / *меньше трат*" top={490} size={92} delay={22} />
      <div
        style={{
          position: "absolute",
          top: 760,
          left: 140,
          right: 140,
          height: 140,
          borderRadius: 70,
          background: `linear-gradient(100deg, ${C.gold} ${shimmer * 100 - 20}%, ${C.goldLight} ${shimmer * 100}%, ${C.gold} ${shimmer * 100 + 20}%)`,
          boxShadow: "0 24px 60px rgba(217,167,95,0.45)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "Inter Display",
          fontWeight: 900,
          fontSize: 56,
          color: C.bg,
          scale: String(btn),
        }}
      >
        coffeepass.kz
      </div>
      <div
        style={{
          position: "absolute",
          top: 930,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          gap: 16,
          opacity: ease(frame, [90, 104]),
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
