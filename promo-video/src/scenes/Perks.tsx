import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Background, C, Captions, Card, CoinIcon, ease, Phone, Sfx, useSpring, Voice, wordAt } from "../theme";

const AVATAR_COLORS = ["#d9a75f", "#c98a5a", "#b9a27e", "#e2b98a", "#a77b52"];

const Avatar: React.FC<{ i: number; delay: number }> = ({ i, delay }) => {
  const s = useSpring(delay, 10);
  return (
    <div
      style={{
        width: 78,
        height: 78,
        borderRadius: 39,
        marginLeft: i === 0 ? 0 : -22,
        background: AVATAR_COLORS[i],
        border: `5px solid ${C.bg}`,
        scale: String(s),
        display: "flex",
        alignItems: "flex-end",
        justifyContent: "center",
        overflow: "hidden",
      }}
    >
      <svg width={60} height={60} viewBox="0 0 64 64">
        <circle cx={32} cy={24} r={13} fill="rgba(20,15,11,0.55)" />
        <path d="M6 64 C6 44 58 44 58 64 Z" fill="rgba(20,15,11,0.55)" />
      </svg>
    </div>
  );
};

/** Bonuses: coins per visit (raffle, freeze) and up to 100% back for inviting friends. */
export const Perks: React.FC = () => {
  const frame = useCurrentFrame();
  const coinsAt = wordAt("perks", "монеты", 14);
  const friendsAt = wordAt("perks", "100%", 60);
  const phone = useSpring(2, 16, 1);
  const drops = [coinsAt - 6, coinsAt + 2, coinsAt + 10];
  const coins = Math.round(
    interpolate(frame, [drops[0] + 10, drops[2] + 12], [0, 30], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }),
  );
  const pct = Math.round(
    interpolate(frame, [friendsAt - 4, friendsAt + 22], [0, 100], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }),
  );
  return (
    <AbsoluteFill>
      <Background glowY={55} />
      <Voice id="perks" />
      <Sfx src="whoosh" at={0} volume={0.35} />
      {drops.map((d) => (
        <Sfx key={d} src="coin" at={d + 10} volume={0.28} />
      ))}
      <Sfx src="success" at={friendsAt + 22} volume={0.35} />
      <Captions id="perks" top={180} size={84} gold={["монеты", "100%", "друзей"]} />

      <Phone src="coins" width={430} x={40} y={640 + (1 - phone) * 800} rotate={-5} zoom={1.05} focusY={0.1} />
      {drops.map((d, i) => {
        const p = ease(frame, [d, d + 12]);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: 150 + i * 80,
              top: 520 + p * 300,
              opacity: frame < d ? 0 : 1 - ease(frame, [d + 10, d + 14]),
              scale: String(1.3 - p * 0.5),
              rotate: `${(1 - p) * 200}deg`,
            }}
          >
            <CoinIcon size={84} />
          </div>
        );
      })}

      <Card delay={coinsAt} from="right" style={{ left: 500, right: 50, top: 700, padding: "28px 30px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <CoinIcon size={70} />
          <div
            style={{
              fontFamily: "Inter Display",
              fontWeight: 900,
              fontSize: 80,
              color: C.goldLight,
              fontVariantNumeric: "tabular-nums",
            }}
          >
            +{coins}
          </div>
        </div>
        <div style={{ fontFamily: "Inter", fontWeight: 600, fontSize: 30, color: C.muted, marginTop: 6 }}>
          🎟️ розыгрыш года подписки
          <br />
          ❄️ заморозка до 7 дней
        </div>
      </Card>

      <Card delay={friendsAt - 8} from="right" style={{ left: 500, right: 50, top: 1010, padding: "28px 30px" }}>
        <div style={{ display: "flex" }}>
          {[0, 1, 2, 3, 4].map((i) => (
            <Avatar key={i} i={i} delay={friendsAt - 4 + i * 3} />
          ))}
        </div>
        <div
          style={{
            fontFamily: "Inter Display",
            fontWeight: 900,
            fontSize: 110,
            lineHeight: 1,
            marginTop: 14,
            color: pct === 100 ? C.goldLight : C.cream,
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {pct}%
        </div>
        <div style={{ height: 14, borderRadius: 7, background: "rgba(245,233,214,0.1)", marginTop: 14 }}>
          <div
            style={{
              width: `${pct}%`,
              height: 14,
              borderRadius: 7,
              background: `linear-gradient(90deg, ${C.gold}, ${C.goldLight})`,
              boxShadow: "0 0 20px rgba(241,201,131,0.6)",
            }}
          />
        </div>
        <div style={{ fontFamily: "Inter", fontWeight: 600, fontSize: 30, color: C.muted, marginTop: 12 }}>
          от цены подписки
          <br />
          за 5 друзей
        </div>
      </Card>
    </AbsoluteFill>
  );
};
