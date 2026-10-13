import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Background, C, Card, CupIcon, ease, Headline, Phone, Sfx, StepBadge, useSpring, Voice } from "../theme";

const PINS: [number, number][] = [
  [118, 236],
  [300, 170],
  [392, 392],
  [196, 470],
  [338, 600],
  [86, 640],
];

const Pin: React.FC<{ x: number; y: number; delay: number }> = ({ x, y, delay }) => {
  const frame = useCurrentFrame();
  const s = useSpring(delay, 9, 0.6);
  const ring = ((frame - delay) % 40) / 40;
  return (
    <div style={{ position: "absolute", left: x - 34, top: y - 84 }}>
      <div
        style={{
          position: "absolute",
          left: 34 - 40,
          top: 84 - 14,
          width: 80,
          height: 28,
          borderRadius: "50%",
          border: `3px solid ${C.goldLight}`,
          opacity: frame > delay + 8 ? 1 - ring : 0,
          scale: String(0.4 + ring * 1.4),
        }}
      />
      <div
        style={{
          width: 68,
          height: 84,
          translate: `0px ${(1 - s) * -160}px`,
          opacity: Math.min(1, s * 2),
          filter: "drop-shadow(0 8px 14px rgba(0,0,0,0.6))",
        }}
      >
        <svg width={68} height={84} viewBox="0 0 68 84">
          <path d="M34 82 C34 82 4 50 4 32 A30 30 0 1 1 64 32 C64 50 34 82 34 82 Z" fill={C.gold} />
          <circle cx={34} cy={31} r={19} fill={C.bg} />
        </svg>
        <div style={{ position: "absolute", left: 17, top: 13 }}>
          <CupIcon size={34} steam={false} color={C.goldLight} />
        </div>
      </div>
    </div>
  );
};

/** Step 2: find a partner café on the map and order food from 1 000 ₸. */
export const Step2: React.FC = () => {
  const frame = useCurrentFrame();
  const phone = useSpring(4, 16, 1);
  return (
    <AbsoluteFill>
      <Background glowX={60} />
      <Voice id="step2" />
      <Sfx src="whoosh" at={0} volume={0.35} />
      {PINS.map((_, i) => (
        <Sfx key={i} src="pop" at={34 + i * 7} volume={0.2} />
      ))}
      <StepBadge n={2} delay={4} />
      <Headline text="Найди кофейню / и закажи *еду*" top={250} size={92} delay={6} />
      <Phone src="map" y={500 + (1 - phone) * 800} zoom={ease(frame, [20, 200], [1, 1.06])} focusY={0.3}>
        {PINS.map(([x, y], i) => (
          <Pin key={i} x={x} y={y} delay={30 + i * 7} />
        ))}
      </Phone>
      <Card delay={95} style={{ left: 90, right: 90, top: 1310, padding: "34px 40px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 30 }}>
          <div
            style={{
              width: 130,
              height: 130,
              borderRadius: 34,
              background: "rgba(217,167,95,0.16)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 76,
            }}
          >
            🥐
          </div>
          <div>
            <div style={{ fontFamily: "Inter", fontWeight: 600, fontSize: 36, color: C.muted }}>
              Еда в чеке от
            </div>
            <div
              style={{
                fontFamily: "Inter Display",
                fontWeight: 900,
                fontSize: 96,
                color: C.goldLight,
                lineHeight: 1,
              }}
            >
              1 000 ₸
            </div>
          </div>
        </div>
      </Card>
    </AbsoluteFill>
  );
};
