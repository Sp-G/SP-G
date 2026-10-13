import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Background, C, Captions, ease, Sfx, Voice } from "../theme";

const COLS = 7;
const DAYS = 30;
const CELL = 112;
const GAP = 14;

/** "Stop! Still paying for every cup?" — impact + a month calendar filling up with receipts. */
export const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const gridW = COLS * CELL + (COLS - 1) * GAP;
  const left0 = (1080 - gridW) / 2;
  const top0 = 700;
  const shake = Math.max(0, 1 - frame / 14);
  const filled = Math.min(DAYS, Math.max(0, Math.floor((frame - 6) / 2) + 1));
  return (
    <AbsoluteFill>
      <Background glowY={45} />
      <Voice id="hook" />
      <Sfx src="impact" at={0} volume={0.7} />
      {[0, 10, 20].map((d) => (
        <Sfx key={d} src="pop" at={8 + d * 2} volume={0.25} />
      ))}
      <AbsoluteFill
        style={{
          translate: `${Math.sin(frame * 2.7) * 18 * shake}px ${Math.cos(frame * 3.1) * 14 * shake}px`,
          scale: String(1 + 0.06 * shake),
        }}
      >
        <Captions id="hook" top={250} size={104} gold={["Стоп", "каждую"]} />
        {Array.from({ length: DAYS }).map((_, i) => {
          const col = i % COLS;
          const row = Math.floor(i / COLS);
          const appear = 6 + i * 2;
          const s = ease(frame, [appear, appear + 6]);
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: left0 + col * (CELL + GAP),
                top: top0 + row * (CELL + GAP),
                width: CELL,
                height: CELL,
                borderRadius: 24,
                background: "rgba(217,120,95,0.16)",
                border: "2px solid rgba(235,140,110,0.5)",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                opacity: s,
                scale: String(0.3 + 0.7 * s),
                rotate: `${(1 - s) * (i % 2 ? 20 : -20)}deg`,
                fontFamily: "Inter",
              }}
            >
              <div style={{ fontSize: 22, fontWeight: 600, color: C.muted }}>{i + 1}</div>
              <div style={{ fontSize: 38, fontWeight: 900, color: "#f0957a" }}>−₸</div>
            </div>
          );
        })}
        <div
          style={{
            position: "absolute",
            top: top0 + 5 * (CELL + GAP) + 40,
            left: 0,
            right: 0,
            textAlign: "center",
            fontFamily: "Inter Display",
            fontWeight: 900,
            fontSize: 64,
            color: "#f0957a",
            opacity: ease(frame, [10, 18]),
          }}
        >
          {filled} чеков в месяц
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
