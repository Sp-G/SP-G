import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Background, C, CupIcon, ease, Headline, Sfx, useSpring, Voice } from "../theme";

const COLS = 7;
const DAYS = 30;
const CELL = 104;
const GAP = 14;
const SWITCH = 98; // frame where the second sentence starts

/** "Coffee every day is expensive" — a month calendar fills with receipts, then collapses into one payment. */
export const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const gridW = COLS * CELL + (COLS - 1) * GAP;
  const left0 = (1080 - gridW) / 2;
  const top0 = 640;
  const collapse = ease(frame, [SWITCH, SWITCH + 18]);
  const one = useSpring(SWITCH + 12, 11);

  return (
    <AbsoluteFill>
      <Background glowY={45} />
      <Voice id="hook" />
      {[0, 6, 12, 18, 24].map((d) => (
        <Sfx key={d} src="pop" at={18 + d * 2.6} volume={0.25} />
      ))}
      <div style={{ opacity: 1 - ease(frame, [SWITCH - 6, SWITCH + 4]) }}>
        <Headline text="Кофе каждый день — *это* *дорого*" top={230} size={96} />
      </div>
      {frame >= SWITCH - 4 && (
        <Headline text="А если платить / *1 раз в месяц?*" top={230} size={96} delay={SWITCH} />
      )}

      {Array.from({ length: DAYS }).map((_, i) => {
        const col = i % COLS;
        const row = Math.floor(i / COLS);
        const x = left0 + col * (CELL + GAP);
        const y = top0 + row * (CELL + GAP);
        const appear = 10 + i * 2.6;
        const s = ease(frame, [appear, appear + 8]);
        const paid = ease(frame, [appear + 4, appear + 10]);
        const cx = 540 - CELL / 2;
        const cy = top0 + 2 * (CELL + GAP);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x + (cx - x) * collapse,
              top: y + (cy - y) * collapse,
              width: CELL,
              height: CELL,
              borderRadius: 22,
              background: paid > 0.5 ? "rgba(217,120,95,0.16)" : "rgba(245,233,214,0.06)",
              border: `2px solid ${paid > 0.5 ? "rgba(235,140,110,0.5)" : "rgba(245,233,214,0.12)"}`,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              opacity: s * (1 - collapse),
              scale: String((0.6 + 0.4 * s) * (1 - collapse * 0.6)),
              fontFamily: "Inter",
            }}
          >
            <div style={{ fontSize: 22, fontWeight: 600, color: C.muted }}>{i + 1}</div>
            <div
              style={{
                fontSize: 34,
                fontWeight: 900,
                color: "#f0957a",
                opacity: paid,
                scale: String(0.5 + paid * 0.5),
              }}
            >
              −₸
            </div>
          </div>
        );
      })}

      {/* running total of daily receipts */}
      <div
        style={{
          position: "absolute",
          top: top0 + 5 * (CELL + GAP) + 30,
          left: 0,
          right: 0,
          textAlign: "center",
          fontFamily: "Inter",
          fontWeight: 700,
          fontSize: 46,
          color: C.muted,
          opacity: ease(frame, [24, 36]) * (1 - collapse),
        }}
      >
        чек за чеком:{" "}
        <span style={{ color: "#f0957a", fontWeight: 900 }}>
          {Math.min(DAYS, Math.max(0, Math.floor((frame - 10) / 2.6) + 1))} из 30 дней
        </span>
      </div>

      {/* one payment */}
      <div
        style={{
          position: "absolute",
          left: 540 - 270,
          top: 700,
          width: 540,
          height: 540,
          borderRadius: 270,
          background: `radial-gradient(circle at 35% 30%, ${C.goldLight}, ${C.gold} 60%, #9b6a2c)`,
          boxShadow: "0 0 140px rgba(217,167,95,0.55)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          scale: String(one),
          opacity: Math.min(1, one * 2),
        }}
      >
        <CupIcon size={170} color={C.bg} />
        <div
          style={{
            fontFamily: "Inter Display",
            fontWeight: 900,
            fontSize: 110,
            color: C.bg,
            lineHeight: 1,
            marginTop: 6,
          }}
        >
          1×
        </div>
        <div style={{ fontFamily: "Inter", fontWeight: 800, fontSize: 40, color: "#3a2512" }}>
          в месяц
        </div>
      </div>
    </AbsoluteFill>
  );
};
