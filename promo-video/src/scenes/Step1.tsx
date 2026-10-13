import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Background, C, Card, ease, Headline, Highlight, Phone, Sfx, StepBadge, useSpring, Voice } from "../theme";

const f = 520.8 / 900; // screenshot px -> phone screen px

/** Step 1: subscribe for 1 490 ₸ a month. */
export const Step1: React.FC = () => {
  const frame = useCurrentFrame();
  const phone = useSpring(4, 16, 1);
  const price = Math.round(
    interpolate(frame, [70, 110], [0, 1490], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
  );
  return (
    <AbsoluteFill>
      <Background />
      <Voice id="step1" />
      <Sfx src="whoosh" at={0} volume={0.35} />
      <Sfx src="coin" at={110} volume={0.35} />
      <StepBadge n={1} delay={4} />
      <Headline text="Оформи *подписку*" top={250} size={86} delay={6} />
      <Phone
        src="profile"
        y={430 + (1 - phone) * 800}
        zoom={ease(frame, [40, 80], [1, 1.12])}
        focusY={0.2}
      >
        <Highlight x={34 * f} y={385 * f} w={830 * f} h={250 * f} delay={50} />
      </Phone>
      <Card delay={62} style={{ left: 110, right: 110, top: 1290, padding: "40px 48px" }}>
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
        <div style={{ fontFamily: "Inter", fontWeight: 500, fontSize: 36, color: C.muted, marginTop: 10 }}>
          Заморозка и отмена — прямо в приложении
        </div>
      </Card>
    </AbsoluteFill>
  );
};
