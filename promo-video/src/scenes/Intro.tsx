import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Background, ease, Logo, Phone, Sfx, Sub, useSpring, Voice } from "../theme";

/** Brand reveal: logo, one-line promise, the app rising into view. */
export const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const logo = useSpring(2, 12);
  const phone = useSpring(16, 16, 1);
  return (
    <AbsoluteFill>
      <Background glowY={30} />
      <Voice id="intro" />
      <Sfx src="whoosh" at={0} volume={0.35} />
      <Sfx src="success" at={22} volume={0.18} />
      <div
        style={{
          position: "absolute",
          top: 170,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          scale: String(0.6 + 0.4 * logo),
          opacity: Math.min(1, logo * 1.5),
        }}
      >
        <div style={{ marginRight: 110 }}>
          <Logo size={128} />
        </div>
      </div>
      <Sub text="Подписка на кофе в кофейнях‑партнёрах" top={440} delay={18} size={46} />
      <Phone
        src="home"
        y={600 + (1 - phone) * 900}
        scrollY={ease(frame, [60, 150], [0, 140])}
        rotate={(1 - phone) * 8}
      />
    </AbsoluteFill>
  );
};
