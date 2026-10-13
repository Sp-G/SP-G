import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Background, C, Card, CupIcon, ease, Headline, Highlight, Phone, Sfx, useSpring, Voice } from "../theme";

const f = 520.8 / 900;
const RING = 220;
const CUP_FRAMES = [80, 108];
const DONE = 134;

/** The app tracks savings; the subscription pays off within a couple of cups. */
export const Savings: React.FC = () => {
  const frame = useCurrentFrame();
  const phone = useSpring(4, 16, 1);
  const progress =
    0.5 * ease(frame, [CUP_FRAMES[0], CUP_FRAMES[0] + 14]) +
    0.5 * ease(frame, [CUP_FRAMES[1], CUP_FRAMES[1] + 14]);
  const r = RING / 2 - 14;
  const circ = 2 * Math.PI * r;
  const done = useSpring(DONE, 10);
  return (
    <AbsoluteFill>
      <Background glowY={40} />
      <Voice id="savings" />
      <Sfx src="whoosh" at={0} volume={0.35} />
      {CUP_FRAMES.map((c) => (
        <Sfx key={c} src="pop" at={c} volume={0.3} />
      ))}
      <Sfx src="success" at={DONE} volume={0.4} />
      <Headline text="Экономия — / *под контролем*" top={200} size={96} delay={4} />
      <Phone src="home" y={470 + (1 - phone) * 800} zoom={ease(frame, [20, 60], [1, 1.1])} focusY={0.45}>
        <Highlight x={34 * f} y={598 * f} w={832 * f} h={392 * f} delay={36} />
      </Phone>
      <Card delay={62} style={{ left: 80, right: 80, top: 1240, padding: "36px 40px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 36 }}>
          <div style={{ position: "relative", width: RING, height: RING }}>
            <svg width={RING} height={RING} style={{ rotate: "-90deg" }}>
              <circle cx={RING / 2} cy={RING / 2} r={r} fill="none" stroke="rgba(245,233,214,0.1)" strokeWidth={22} />
              <circle
                cx={RING / 2}
                cy={RING / 2}
                r={r}
                fill="none"
                stroke={frame >= DONE ? C.green : C.goldLight}
                strokeWidth={22}
                strokeLinecap="round"
                strokeDasharray={circ}
                strokeDashoffset={circ * (1 - progress)}
              />
            </svg>
            <div
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontFamily: "Inter Display",
                fontWeight: 900,
                fontSize: 50,
                color: frame >= DONE ? C.green : C.cream,
              }}
            >
              {Math.round(progress * 100)}%
            </div>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: "Inter", fontWeight: 700, fontSize: 30, letterSpacing: 3, color: C.muted }}>
              ОКУПАЕМОСТЬ
            </div>
            <div style={{ display: "flex", gap: 14, margin: "14px 0" }}>
              {CUP_FRAMES.map((c) => (
                <div key={c} style={{ scale: String(ease(frame, [c - 4, c + 6])) }}>
                  <CupIcon size={84} steam={false} />
                </div>
              ))}
            </div>
            <div
              style={{
                fontFamily: "Inter Display",
                fontWeight: 900,
                fontSize: 50,
                color: C.green,
                opacity: Math.min(1, done * 2),
                translate: `0px ${(1 - done) * 20}px`,
              }}
            >
              ✓ Окупилась!
            </div>
          </div>
        </div>
      </Card>
    </AbsoluteFill>
  );
};
