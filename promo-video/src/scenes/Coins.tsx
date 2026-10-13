import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Background, C, Card, CoinIcon, ease, Headline, Phone, Sfx, useSpring, Voice } from "../theme";

const DROPS = [26, 40, 54];

const Reward: React.FC<{ icon: string; title: string; value: string; cost: number }> = ({
  icon,
  title,
  value,
  cost,
}) => (
  <div style={{ display: "flex", alignItems: "center", gap: 26 }}>
    <div
      style={{
        width: 104,
        height: 104,
        borderRadius: 28,
        background: "rgba(217,167,95,0.16)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 60,
      }}
    >
      {icon}
    </div>
    <div style={{ flex: 1 }}>
      <div style={{ fontFamily: "Inter", fontWeight: 600, fontSize: 32, color: C.muted }}>{title}</div>
      <div style={{ fontFamily: "Inter Display", fontWeight: 900, fontSize: 52, color: C.goldLight, lineHeight: 1.1 }}>
        {value}
      </div>
    </div>
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <CoinIcon size={46} />
      <span style={{ fontFamily: "Inter", fontWeight: 800, fontSize: 40, color: C.cream }}>{cost}</span>
    </div>
  </div>
);

/** Coins for every visit: spend them on a freeze or a yearly-subscription raffle ticket. */
export const Coins: React.FC = () => {
  const frame = useCurrentFrame();
  const phone = useSpring(4, 16, 1);
  const count = Math.round(
    interpolate(frame, [DROPS[0] + 14, DROPS[2] + 18], [0, 30], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }),
  );
  const phoneY = 470 + (1 - phone) * 800;
  return (
    <AbsoluteFill>
      <Background glowY={50} />
      <Voice id="coins" />
      <Sfx src="whoosh" at={0} volume={0.35} />
      {DROPS.map((d) => (
        <Sfx key={d} src="coin" at={d + 14} volume={0.3} />
      ))}
      <Headline text="Монеты за / *каждый визит*" top={180} size={96} delay={4} />
      <Phone src="coins" width={480} y={phoneY} zoom={1.05} focusY={0.1} />

      {/* coins flying into the balance */}
      {DROPS.map((d, i) => {
        const p = ease(frame, [d, d + 16]);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: 300 + i * 90 + (1 - p) * (i - 1) * 140,
              top: 280 + p * 340,
              opacity: frame < d ? 0 : 1 - ease(frame, [d + 14, d + 18]),
              scale: String(1.4 - p * 0.6),
              rotate: `${(1 - p) * 180}deg`,
            }}
          >
            <CoinIcon size={90} />
          </div>
        );
      })}
      <div
        style={{
          position: "absolute",
          left: 540 + 70,
          top: phoneY + 140,
          padding: "14px 28px",
          borderRadius: 100,
          background: C.gold,
          fontFamily: "Inter Display",
          fontWeight: 900,
          fontSize: 54,
          color: C.bg,
          boxShadow: "0 16px 40px rgba(0,0,0,0.5)",
          opacity: ease(frame, [DROPS[0] + 12, DROPS[0] + 18]),
          scale: String(1 + 0.12 * Math.max(0, Math.sin(((frame - DROPS[0]) / 14) * Math.PI)) * (frame < DROPS[2] + 20 ? 1 : 0)),
        }}
      >
        +{count}
      </div>
      <Card delay={92} from="left" style={{ left: 70, right: 70, top: 1120, padding: "28px 34px" }}>
        <Reward icon="🎟️" title="Розыгрыш подписки" value="на целый год" cost={100} />
      </Card>
      <Card delay={150} from="right" style={{ left: 70, right: 70, top: 1340, padding: "28px 34px" }}>
        <Reward icon="❄️" title="Заморозка подписки" value="до 7 дней паузы" cost={150} />
      </Card>
    </AbsoluteFill>
  );
};
