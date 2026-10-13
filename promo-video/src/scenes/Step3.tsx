import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import {
  Background,
  C,
  Card,
  CoinIcon,
  CupIcon,
  ease,
  Captions,
  Phone,
  Sfx,
  StepBadge,
  useSpring,
  Voice,
  wordAt,
} from "../theme";

const f = 520.8 / 900;
// scanner viewfinder in phone-screen px
const VF = { x: 127 * f, y: 316 * f, w: (770 - 127) * f, h: (1300 - 316) * f };
const OK = wordAt("step3", "бесплатно", 100) - 4;
const SCAN_START = 24;
const SCAN_END = Math.min(OK - 8, 64);

const Receipt: React.FC = () => (
  <div
    style={{
      width: 250,
      padding: "26px 22px 34px",
      background: "#f7f1e6",
      fontFamily: "Inter",
      color: "#3a2c20",
      boxShadow: "0 20px 40px rgba(0,0,0,0.5)",
      clipPath:
        "polygon(0 0,100% 0,100% 97%,92% 100%,84% 97%,76% 100%,68% 97%,60% 100%,52% 97%,44% 100%,36% 97%,28% 100%,20% 97%,12% 100%,4% 97%,0 100%)",
    }}
  >
    <div style={{ textAlign: "center", fontWeight: 900, fontSize: 22, letterSpacing: 2 }}>КОФЕЙНЯ</div>
    <div style={{ textAlign: "center", fontSize: 13, opacity: 0.6, marginBottom: 14 }}>кассовый чек</div>
    {[
      ["Круассан", "850"],
      ["Сэндвич", "250"],
    ].map(([a, b]) => (
      <div key={a} style={{ display: "flex", justifyContent: "space-between", fontSize: 19, margin: "6px 0" }}>
        <span>{a}</span>
        <span style={{ fontWeight: 700 }}>{b}</span>
      </div>
    ))}
    {[0, 1, 2].map((i) => (
      <div key={i} style={{ height: 8, borderRadius: 4, background: "#ddd2c0", margin: "12px 0", width: `${90 - i * 18}%` }} />
    ))}
    <div style={{ borderTop: "2px dashed #b9ab96", marginTop: 14, paddingTop: 10, display: "flex", justifyContent: "space-between", fontWeight: 900, fontSize: 22 }}>
      <span>ИТОГО</span>
      <span>1 100 ₸</span>
    </div>
  </div>
);

/** Step 3: scan the receipt — the drink is free. */
export const Step3: React.FC = () => {
  const frame = useCurrentFrame();
  const phone = useSpring(2, 16, 1);
  const receipt = useSpring(10, 15);
  const ok = useSpring(OK, 10);
  const scan = ease(frame, [SCAN_START, SCAN_END]);
  const scanning = frame >= SCAN_START && frame < SCAN_END + 4;
  return (
    <AbsoluteFill>
      <Background />
      <Voice id="step3" />
      <Sfx src="whoosh" at={0} volume={0.35} />
      <Sfx src="whoosh" at={10} volume={0.2} />
      <Sfx src="success" at={OK} volume={0.45} />
      <Sfx src="coin" at={OK + 22} volume={0.35} />
      <StepBadge n={3} delay={2} />
      <Captions id="step3" top={240} size={86} gold={["чек", "бесплатно"]} />
      <Phone src="scanner" y={500 + (1 - phone) * 800}>
        <div
          style={{
            position: "absolute",
            left: VF.x + VF.w / 2 - 125,
            top: VF.y + 40 + (1 - receipt) * 700,
            rotate: `${(1 - receipt) * 14 - 2}deg`,
          }}
        >
          <Receipt />
        </div>
        {scanning && (
          <div
            style={{
              position: "absolute",
              left: VF.x,
              width: VF.w,
              top: VF.y + VF.h * scan,
              height: 6,
              borderRadius: 3,
              background: C.goldLight,
              boxShadow: `0 0 30px 10px rgba(241,201,131,0.6)`,
            }}
          />
        )}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "rgba(20,15,11,0.72)",
            opacity: ease(frame, [OK, OK + 8]),
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 260 - 110,
            top: VF.y + VF.h / 2 - 110,
            width: 220,
            height: 220,
            borderRadius: 110,
            background: C.gold,
            boxShadow: "0 0 80px rgba(217,167,95,0.8)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            scale: String(ok),
          }}
        >
          <svg width={120} height={100} viewBox="0 0 110 90">
            <path
              d="M8 48 L40 78 L104 6"
              fill="none"
              stroke={C.bg}
              strokeWidth={16}
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeDasharray={170}
              strokeDashoffset={170 * (1 - ease(frame, [OK + 4, OK + 16]))}
            />
          </svg>
        </div>
      </Phone>
      <Card delay={OK + 6} style={{ left: 90, right: 90, top: 1330, padding: "30px 40px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
          <CupIcon size={120} />
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: "Inter", fontWeight: 600, fontSize: 36, color: C.muted }}>Напиток</div>
            <div style={{ fontFamily: "Inter Display", fontWeight: 900, fontSize: 92, color: C.goldLight, lineHeight: 1 }}>
              0 ₸
            </div>
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "12px 20px",
              borderRadius: 100,
              background: "rgba(127,211,154,0.15)",
              opacity: ease(frame, [OK + 20, OK + 28]),
              scale: String(0.6 + 0.4 * ease(frame, [OK + 20, OK + 28])),
            }}
          >
            <CoinIcon size={44} />
            <span style={{ fontFamily: "Inter", fontWeight: 800, fontSize: 36, color: C.green }}>+10</span>
          </div>
        </div>
      </Card>
    </AbsoluteFill>
  );
};
