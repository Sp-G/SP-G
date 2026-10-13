import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Background, C, Card, ease, Headline, Sfx, useSpring, Voice } from "../theme";

const TIERS = [
  { friends: 1, pct: 20, at: 0.2 },
  { friends: 3, pct: 50, at: 0.5 },
  { friends: 5, pct: 100, at: 1 },
];
const AVATAR_COLORS = ["#d9a75f", "#c98a5a", "#b9a27e", "#e2b98a", "#a77b52"];
const BAR_L = 120;
const BAR_W = 840;
const BAR_Y = 1010;
const FILL_START = 30;
const FILL_END = 120;

const Avatar: React.FC<{ i: number; delay: number }> = ({ i, delay }) => {
  const s = useSpring(delay, 10);
  return (
    <div
      style={{
        width: 84,
        height: 84,
        borderRadius: 42,
        marginLeft: i === 0 ? 0 : -24,
        background: AVATAR_COLORS[i],
        border: `5px solid ${C.bg}`,
        scale: String(s),
        display: "flex",
        alignItems: "flex-end",
        justifyContent: "center",
        overflow: "hidden",
      }}
    >
      <svg width={64} height={64} viewBox="0 0 64 64">
        <circle cx={32} cy={24} r={13} fill="rgba(20,15,11,0.55)" />
        <path d="M6 64 C6 44 58 44 58 64 Z" fill="rgba(20,15,11,0.55)" />
      </svg>
    </div>
  );
};

/** Invite friends: up to 100% of the subscription price back as bonus balance. */
export const Friends: React.FC = () => {
  const frame = useCurrentFrame();
  const fill = interpolate(frame, [FILL_START, FILL_END], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const pct = Math.round(fill * 100);
  return (
    <AbsoluteFill>
      <Background glowY={55} />
      <Voice id="friends" />
      <Sfx src="whoosh" at={0} volume={0.35} />
      {TIERS.map((t) => (
        <Sfx key={t.pct} src="pop" at={FILL_START + t.at * (FILL_END - FILL_START)} volume={0.3} />
      ))}
      <Sfx src="success" at={FILL_END} volume={0.3} />
      <Headline text="Зови *друзей* —" top={220} size={100} delay={4} />
      <Headline text="верни до *100%*" top={340} size={100} delay={12} />
      <div
        style={{
          position: "absolute",
          top: 500,
          left: 0,
          right: 0,
          textAlign: "center",
          fontFamily: "Inter Display",
          fontWeight: 900,
          fontSize: 230,
          lineHeight: 1,
          color: C.goldLight,
          textShadow: "0 0 80px rgba(217,167,95,0.5)",
          fontVariantNumeric: "tabular-nums",
          opacity: ease(frame, [FILL_START - 10, FILL_START]),
        }}
      >
        {pct}%
      </div>

      {/* progress track */}
      <div
        style={{
          position: "absolute",
          left: BAR_L,
          top: BAR_Y,
          width: BAR_W,
          height: 26,
          borderRadius: 13,
          background: "rgba(245,233,214,0.1)",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: BAR_L,
          top: BAR_Y,
          width: BAR_W * fill,
          height: 26,
          borderRadius: 13,
          background: `linear-gradient(90deg, ${C.gold}, ${C.goldLight})`,
          boxShadow: "0 0 30px rgba(241,201,131,0.6)",
        }}
      />
      {TIERS.map((t, k) => {
        const x = BAR_L + BAR_W * t.at;
        const reached = fill >= t.at - 0.001;
        const reachFrame = FILL_START + t.at * (FILL_END - FILL_START);
        return (
          <React.Fragment key={t.pct}>
            <div
              style={{
                position: "absolute",
                left: x - 30,
                top: BAR_Y - 17,
                width: 60,
                height: 60,
                borderRadius: 30,
                background: reached ? C.goldLight : "#3a2d23",
                border: `6px solid ${C.bg}`,
                scale: String(1 + 0.3 * Math.max(0, 1 - Math.abs(frame - reachFrame) / 6)),
              }}
            />
            <div
              style={{
                position: "absolute",
                left: x - 160 - (k === 2 ? 70 : 0),
                width: 320,
                top: BAR_Y - 130,
                display: "flex",
                justifyContent: "center",
              }}
            >
              {Array.from({ length: t.friends }).map((_, i) => (
                <Avatar key={i} i={i} delay={reachFrame - 8 + i * 2} />
              ))}
            </div>
            <div
              style={{
                position: "absolute",
                left: x - 140 - (k === 2 ? 70 : 0),
                width: 280,
                top: BAR_Y + 60,
                textAlign: "center",
                fontFamily: "Inter",
                opacity: reached ? 1 : 0.35,
              }}
            >
              <div style={{ fontFamily: "Inter Display", fontWeight: 900, fontSize: 60, color: reached ? C.goldLight : C.muted }}>
                {t.pct}%
              </div>
              <div style={{ fontWeight: 600, fontSize: 32, color: C.muted }}>
                {t.friends} {t.friends === 1 ? "друг" : t.friends === 3 ? "друга" : "друзей"}
              </div>
            </div>
          </React.Fragment>
        );
      })}

      <Card delay={FILL_END - 4} style={{ left: 90, right: 90, top: 1320, padding: "34px 40px" }}>
        <div style={{ fontFamily: "Inter", fontWeight: 600, fontSize: 38, color: C.cream, lineHeight: 1.3 }}>
          от цены подписки — на{" "}
          <span style={{ color: C.goldLight, fontWeight: 800 }}>бонусный баланс</span>
        </div>
        <div style={{ fontFamily: "Inter", fontWeight: 500, fontSize: 30, color: C.muted, marginTop: 14 }}>
          за друзей с оплаченной подпиской
        </div>
      </Card>
    </AbsoluteFill>
  );
};
