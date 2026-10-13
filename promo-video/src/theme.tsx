import { loadFont } from "@remotion/fonts";
import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Audio } from "@remotion/media";
import timings from "./vo-timings.json";
import captions from "./vo-captions.json";

const FONT_FILES: [string, string][] = [
  ["Inter-Regular", "400"],
  ["Inter-Medium", "500"],
  ["Inter-SemiBold", "600"],
  ["Inter-Bold", "700"],
  ["Inter-ExtraBold", "800"],
  ["Inter-Black", "900"],
];
FONT_FILES.forEach(([file, weight]) =>
  loadFont({ family: "Inter", url: staticFile(`fonts/${file}.otf`), weight }),
);
[
  ["InterDisplay-Bold", "700"],
  ["InterDisplay-ExtraBold", "800"],
  ["InterDisplay-Black", "900"],
].forEach(([file, weight]) =>
  loadFont({ family: "Inter Display", url: staticFile(`fonts/${file}.otf`), weight }),
);

export const C = {
  bg: "#140f0b",
  bg2: "#221912",
  card: "#2a2019",
  cardBorder: "rgba(232, 190, 120, 0.18)",
  gold: "#d9a75f",
  goldLight: "#f1c983",
  cream: "#f5e9d6",
  muted: "#a8977f",
  green: "#7fd39a",
};

export const FPS = 30;
export const TRANSITION = 8;
const LEAD = 4; // frames before the voice line starts
const TAIL = 8; // frames held after the voice line ends

export type SceneId = keyof typeof timings;
export const voFrames = (id: SceneId) => Math.ceil(timings[id] * FPS);
export const sceneFrames = (id: SceneId, extra = 0) =>
  LEAD + voFrames(id) + TAIL + TRANSITION + extra;

export const SCENES: { id: SceneId; extra?: number }[] = [
  { id: "hook" },
  { id: "intro" },
  { id: "step1" },
  { id: "step2" },
  { id: "step3", extra: 6 },
  { id: "perks" },
  { id: "cta", extra: 36 },
];

export const sceneStarts = () => {
  let t = 0;
  return SCENES.map((s) => {
    const start = t;
    t += sceneFrames(s.id, s.extra) - TRANSITION;
    return { ...s, start, duration: sceneFrames(s.id, s.extra) };
  });
};
export const TOTAL_FRAMES = (() => {
  const all = sceneStarts();
  const last = all[all.length - 1];
  return last.start + last.duration;
})();

/** Voice line ranges on the global timeline, used for music ducking. */
export const voRanges = () =>
  sceneStarts().map((s) => [s.start + LEAD, s.start + LEAD + voFrames(s.id)] as const);

const out = Easing.bezier(0.16, 1, 0.3, 1);
export const ease = (
  frame: number,
  input: [number, number],
  output: [number, number] = [0, 1],
) =>
  interpolate(frame, input, output, {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: out,
  });

export const useSpring = (delay: number, damping = 14, mass = 0.7) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - delay, fps, config: { damping, mass } });
};

/** Voice line of a scene, starting after the transition-in has settled. */
export const Voice: React.FC<{ id: SceneId }> = ({ id }) => (
  <Sequence from={LEAD} layout="none">
    <Audio src={staticFile(`vo/${id}.mp3`)} volume={1} />
  </Sequence>
);

export const Sfx: React.FC<{ src: string; at: number; volume?: number }> = ({
  src,
  at,
  volume = 0.5,
}) => (
  <Sequence from={at} layout="none">
    <Audio src={staticFile(`sfx/${src}.wav`)} volume={volume} />
  </Sequence>
);

/** Warm espresso backdrop with a slow-drifting golden glow and film grain. */
export const Background: React.FC<{ glowX?: number; glowY?: number }> = ({
  glowX = 50,
  glowY = 38,
}) => {
  const frame = useCurrentFrame();
  const dx = Math.sin(frame / 50) * 6;
  const dy = Math.cos(frame / 65) * 4;
  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${glowX + dx}% ${glowY + dy}%, rgba(217,167,95,0.28) 0%, rgba(120,72,30,0.14) 32%, rgba(20,15,11,0) 62%)`,
        }}
      />
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at 50% 120%, rgba(217,167,95,0.16), rgba(0,0,0,0) 55%)",
        }}
      />
      <AbsoluteFill
        style={{
          opacity: 0.06,
          backgroundImage:
            "repeating-radial-gradient(circle at 17% 32%, #fff 0px, transparent 1px, transparent 3px)",
          backgroundPosition: `${(frame * 37) % 7}px ${(frame * 53) % 5}px`,
        }}
      />
    </AbsoluteFill>
  );
};

/** Animated headline: each word rises in with a stagger. Words wrapped in *stars* are gold. */
export const Headline: React.FC<{
  text: string;
  delay?: number;
  size?: number;
  top?: number;
  align?: "center" | "left";
}> = ({ text, delay = 0, size = 92, top = 230, align = "center" }) => {
  const frame = useCurrentFrame();
  const words = text.split(" ");
  return (
    <div
      style={{
        position: "absolute",
        top,
        left: 80,
        right: 80,
        textAlign: align,
        fontFamily: "Inter Display",
        fontWeight: 900,
        fontSize: size,
        lineHeight: 1.04,
        letterSpacing: -2,
        color: C.cream,
      }}
    >
      {words.map((w, i) => {
        const gold = w.startsWith("*");
        const clean = w.replace(/\*/g, "");
        const d = delay + i * 3;
        if (clean === "/") return <br key={i} />;
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              marginRight: size * 0.24,
              opacity: ease(frame, [d, d + 10]),
              translate: `0px ${ease(frame, [d, d + 16], [size * 0.6, 0])}px`,
              filter: `blur(${ease(frame, [d, d + 12], [10, 0])}px)`,
              color: gold ? C.goldLight : C.cream,
            }}
          >
            {clean}
          </span>
        );
      })}
    </div>
  );
};

export const Sub: React.FC<{ text: string; delay?: number; top: number; size?: number }> = ({
  text,
  delay = 8,
  top,
  size = 44,
}) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        position: "absolute",
        top,
        left: 90,
        right: 90,
        textAlign: "center",
        fontFamily: "Inter",
        fontWeight: 500,
        fontSize: size,
        lineHeight: 1.25,
        color: C.muted,
        opacity: ease(frame, [delay, delay + 14]),
        translate: `0px ${ease(frame, [delay, delay + 18], [24, 0])}px`,
      }}
    >
      {text}
    </div>
  );
};

export const StepBadge: React.FC<{ n: number; delay?: number; top?: number }> = ({
  n,
  delay = 0,
  top = 120,
}) => {
  const frame = useCurrentFrame();
  const s = useSpring(delay, 12);
  return (
    <div
      style={{
        position: "absolute",
        top,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        gap: 18,
        alignItems: "center",
      }}
    >
      <div
        style={{
          scale: String(s),
          display: "flex",
          alignItems: "center",
          gap: 16,
          padding: "14px 30px 14px 16px",
          borderRadius: 100,
          background: "rgba(217,167,95,0.14)",
          border: `2px solid ${C.cardBorder}`,
        }}
      >
        <div
          style={{
            width: 54,
            height: 54,
            borderRadius: 27,
            background: C.gold,
            color: C.bg,
            fontFamily: "Inter Display",
            fontWeight: 900,
            fontSize: 32,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {n}
        </div>
        <div
          style={{
            fontFamily: "Inter",
            fontWeight: 800,
            fontSize: 30,
            letterSpacing: 4,
            color: C.goldLight,
          }}
        >
          ШАГ {n} ИЗ 3
        </div>
      </div>
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          style={{
            width: i === n ? 46 : 14,
            height: 14,
            borderRadius: 7,
            background: i <= n ? C.gold : "rgba(245,233,214,0.2)",
            opacity: ease(frame, [delay + 6 + i * 2, delay + 14 + i * 2]),
          }}
        />
      ))}
    </div>
  );
};

export const PHONE_W = 560;
export const SCREEN_RATIO = 1839 / 900;

/**
 * iPhone-style frame showing an app screenshot.
 * `zoom` / `focusY` (0..1) let a scene push into a part of the screen; `scrollY` pans the image.
 */
export const Phone: React.FC<{
  src: string;
  x?: number;
  y: number;
  width?: number;
  zoom?: number;
  focusY?: number;
  scrollY?: number;
  rotate?: number;
  children?: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ src, x, y, width = PHONE_W, zoom = 1, focusY = 0, scrollY = 0, rotate = 0, children, style }) => {
  const bezel = width * 0.035;
  const screenW = width - bezel * 2;
  const statusH = screenW * 0.085;
  const screenH = screenW * SCREEN_RATIO + statusH;
  const h = screenH + bezel * 2;
  const left = x ?? (1080 - width) / 2;
  return (
    <div
      style={{
        position: "absolute",
        left,
        top: y,
        width,
        height: h,
        borderRadius: width * 0.14,
        background: "linear-gradient(145deg, #4a3b30, #17110d 40%, #3b2e25)",
        padding: bezel,
        boxShadow:
          "0 60px 120px rgba(0,0,0,0.65), 0 0 0 2px rgba(241,201,131,0.25), inset 0 0 0 2px rgba(255,255,255,0.06)",
        rotate: `${rotate}deg`,
        ...style,
      }}
    >
      <div
        style={{
          position: "relative",
          width: screenW,
          height: screenH,
          borderRadius: width * 0.11,
          overflow: "hidden",
          background: "#1b1612",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: statusH,
            left: 0,
            width: screenW,
            height: screenH - statusH,
            overflow: "hidden",
          }}
        >
          <Img
            src={staticFile(`screens/${src}.jpg`)}
            style={{
              position: "absolute",
              width: screenW,
              left: 0,
              top: -scrollY,
              scale: String(zoom),
              transformOrigin: `50% ${focusY * 100}%`,
            }}
          />
          {children}
        </div>
        {/* status bar */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: statusH,
            background: "#1b1612",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: `0 ${screenW * 0.09}px`,
            fontFamily: "Inter",
            fontWeight: 700,
            fontSize: statusH * 0.4,
            color: C.cream,
          }}
        >
          <span>9:41</span>
          <span style={{ letterSpacing: 2, fontSize: statusH * 0.3 }}>●●●● 5G ▮</span>
        </div>
        <div
          style={{
            position: "absolute",
            top: statusH * 0.18,
            left: screenW / 2 - screenW * 0.16,
            width: screenW * 0.32,
            height: statusH * 0.62,
            borderRadius: 100,
            background: "#000",
          }}
        />
      </div>
    </div>
  );
};

/** Glowing outline that draws attention to a region inside the phone screen (coords in screen px). */
export const Highlight: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  delay: number;
  radius?: number;
}> = ({ x, y, w, h, delay, radius = 24 }) => {
  const frame = useCurrentFrame();
  const p = ease(frame, [delay, delay + 14]);
  const pulse = 1 + Math.sin((frame - delay) / 6) * 0.015 * p;
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        width: w,
        height: h,
        borderRadius: radius,
        border: `5px solid ${C.goldLight}`,
        boxShadow: `0 0 40px rgba(241,201,131,0.75), inset 0 0 30px rgba(241,201,131,0.25)`,
        opacity: p,
        scale: String((1.15 - 0.15 * p) * pulse),
      }}
    />
  );
};

/** Rounded infographic card. */
export const Card: React.FC<{
  children: React.ReactNode;
  style?: React.CSSProperties;
  delay: number;
  from?: "left" | "right" | "bottom";
}> = ({ children, style, delay, from = "bottom" }) => {
  const s = useSpring(delay, 15);
  const off = (1 - s) * 220;
  const translate =
    from === "left" ? `${-off}px 0px` : from === "right" ? `${off}px 0px` : `0px ${off}px`;
  return (
    <div
      style={{
        position: "absolute",
        borderRadius: 36,
        background: "linear-gradient(160deg, rgba(58,44,34,0.97), rgba(30,23,18,0.97))",
        border: `2px solid ${C.cardBorder}`,
        boxShadow: "0 30px 70px rgba(0,0,0,0.55)",
        opacity: Math.min(1, s * 1.4),
        translate,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

export const Logo: React.FC<{ size?: number }> = ({ size = 120 }) => {
  const frame = useCurrentFrame();
  const draw = ease(frame, [8, 26]);
  return (
    <div
      style={{
        position: "relative",
        fontFamily: "Inter Display",
        fontWeight: 800,
        fontSize: size,
        lineHeight: 0.88,
        color: C.cream,
        letterSpacing: -size * 0.03,
      }}
    >
      coffee
      <br />
      pass
      <svg
        width={size * 1.1}
        height={size * 0.9}
        viewBox="0 0 110 90"
        style={{ position: "absolute", left: size * 2.05, top: size * 0.8 }}
      >
        <path
          d="M8 48 L40 78 L104 6"
          fill="none"
          stroke={C.gold}
          strokeWidth={16}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={170}
          strokeDashoffset={170 * (1 - draw)}
        />
      </svg>
    </div>
  );
};

export const CupIcon: React.FC<{ size: number; steam?: boolean; color?: string }> = ({
  size,
  steam = true,
  color = C.gold,
}) => {
  const frame = useCurrentFrame();
  return (
    <svg width={size} height={size} viewBox="0 0 100 100">
      {steam &&
        [30, 46, 62].map((x, i) => (
          <path
            key={x}
            d={`M${x} 30 C ${x - 7} 22, ${x + 7} 16, ${x} 6`}
            fill="none"
            stroke={color}
            strokeWidth={4}
            strokeLinecap="round"
            opacity={0.35 + 0.35 * Math.sin(frame / 7 + i * 2)}
            transform={`translate(0 ${Math.sin(frame / 9 + i) * 2})`}
          />
        ))}
      <path d="M16 38 H76 V64 C76 80 64 90 46 90 C28 90 16 80 16 64 Z" fill={color} />
      <path
        d="M76 46 C92 46 92 70 74 70"
        fill="none"
        stroke={color}
        strokeWidth={7}
        strokeLinecap="round"
      />
    </svg>
  );
};

export const CoinIcon: React.FC<{ size: number }> = ({ size }) => (
  <div
    style={{
      width: size,
      height: size,
      borderRadius: size / 2,
      background: `radial-gradient(circle at 35% 30%, #ffe2a6, ${C.gold} 55%, #9b6a2c)`,
      boxShadow: `inset 0 0 0 ${size * 0.07}px rgba(255,236,190,0.6), 0 ${size * 0.08}px ${size * 0.25}px rgba(0,0,0,0.4)`,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontFamily: "Inter Display",
      fontWeight: 900,
      fontSize: size * 0.5,
      color: "#6b4518",
    }}
  >
    M
  </div>
);

/**
 * Voice-synced kinetic captions: each word pops in exactly when it is spoken,
 * the word being spoken glows gold. Words not yet spoken keep their space so lines never reflow.
 */
export const Captions: React.FC<{ id: SceneId; top?: number; size?: number; gold?: string[] }> = ({
  id,
  top = 230,
  size = 92,
  gold = [],
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = (captions as Record<string, { text: string; start: number; end: number }[]>)[id];
  return (
    <div
      style={{
        position: "absolute",
        top,
        left: 70,
        right: 70,
        textAlign: "center",
        fontFamily: "Inter Display",
        fontWeight: 900,
        fontSize: size,
        lineHeight: 1.08,
        letterSpacing: -1.5,
        color: C.cream,
        textShadow: "0 6px 30px rgba(0,0,0,0.55)",
      }}
    >
      {words.map((w, i) => {
        const at = LEAD + w.start * fps - 2;
        const end = LEAD + (words[i + 1]?.start ?? w.end + 0.3) * fps - 2;
        const s = spring({ frame: frame - at, fps, config: { damping: 11, mass: 0.5 } });
        const active = frame >= at && frame < end;
        const isGold = gold.some((g) => w.text.toLowerCase().includes(g.toLowerCase()));
        return (
          <span
            key={i}
            style={{
              display: frame < at ? "none" : "inline-block",
              marginRight: size * 0.22,
              scale: String((0.4 + 0.6 * Math.min(1, s)) * (active ? 1.08 : 1)),
              translate: `0px ${(1 - Math.min(1, s)) * 30}px`,
              color: active || isGold ? C.goldLight : C.cream,
            }}
          >
            {w.text}
          </span>
        );
      })}
    </div>
  );
};

/** Frame (scene-relative) at which the first caption word containing `text` is spoken. */
export const wordAt = (id: SceneId, text: string, fallback = 0) => {
  const words = (captions as Record<string, { text: string; start: number }[]>)[id];
  const w = words.find((x) => x.text.toLowerCase().includes(text.toLowerCase()));
  return w ? Math.round(LEAD + w.start * FPS) : fallback;
};
