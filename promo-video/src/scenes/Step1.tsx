import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Background, C, Captions, Card, ease, Highlight, Phone, Sfx, StepBadge, useSpring, Voice } from "../theme";

const f = 520.8 / 900; // screenshot px -> phone screen px

/** Step 1: subscribe. */
export const Step1: React.FC = () => {
  const frame = useCurrentFrame();
  const phone = useSpring(2, 16, 1);
  const price = Math.round(
    interpolate(frame, [30, 56], [0, 1490], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
  );
  return (
    <AbsoluteFill>
      <Background />
      <Voice id="step1" />
      <Sfx src="whoosh" at={0} volume={0.35} />
      <Sfx src="coin" at={56} volume={0.35} />
      <StepBadge n={1} delay={2} />
      <Captions id="step1" top={240} size={92} gold={["подписку"]} />
      <Phone src="profile" y={520 + (1 - phone) * 800} zoom={ease(frame, [14, 50], [1, 1.12])} focusY={0.2}>
        <Highlight x={34 * f} y={385 * f} w={830 * f} h={250 * f} delay={20} />
      </Phone>
      <Card delay={26} style={{ left: 110, right: 110, top: 1290, padding: "40px 48px" }}>
        <div style={{ fontFamily: "Inter", fontWeight: 700, fontSize: 30, letterSpacing: 4, color: C.muted }}>
          ТАРИФ «ЛАЙТ»
        </div>
        <div style={{ display: "flex", alignItems: "baseline", gap: 18, marginTop: 6 }}>
          <div
            style={{
              fontFamily: "Inter Display",
              fontWeight: 900,
              fontSize: 150,
              color: C.goldLight,
              lineHeight: 1,
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {price.toLocaleString("ru-RU")} ₸
          </div>
          <div style={{ fontFamily: "Inter", fontWeight: 700, fontSize: 48, color: C.cream }}>/ мес</div>
        </div>
      </Card>
    </AbsoluteFill>
  );
};
