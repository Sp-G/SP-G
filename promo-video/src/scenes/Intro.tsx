import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Background, Captions, ease, Logo, Phone, Sfx, useSpring, Voice, wordAt } from "../theme";

/** "Then you need Coffee Pass — coffee by subscription." Brand slam + the app. */
export const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const brandAt = wordAt("intro", "Coffee", 30);
  const logo = useSpring(brandAt - 2, 9);
  const phone = useSpring(6, 16, 1);
  return (
    <AbsoluteFill>
      <Background glowY={30} />
      <Voice id="intro" />
      <Sfx src="whoosh" at={0} volume={0.35} />
      <Sfx src="impact" at={brandAt - 2} volume={0.5} />
      <Captions id="intro" top={170} size={80} gold={["Coffee", "подписке"]} />
      <div
        style={{
          position: "absolute",
          top: 520,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          scale: String(2.2 - 1.2 * logo),
          opacity: Math.min(1, logo * 2),
        }}
      >
        <div style={{ marginRight: 100 }}>
          <Logo size={104} />
        </div>
      </div>
      <Phone
        src="home"
        y={800 + (1 - phone) * 900}
        scrollY={ease(frame, [40, 120], [0, 120])}
        rotate={(1 - phone) * 8}
      />
    </AbsoluteFill>
  );
};
