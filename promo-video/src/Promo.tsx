import React from "react";
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { AbsoluteFill, interpolate, staticFile } from "remotion";
import { Audio } from "@remotion/media";
import { C, sceneFrames, SCENES, SceneId, TRANSITION, voRanges } from "./theme";
import { Hook } from "./scenes/Hook";
import { Intro } from "./scenes/Intro";
import { Step1 } from "./scenes/Step1";
import { Step2 } from "./scenes/Step2";
import { Step3 } from "./scenes/Step3";
import { Coins } from "./scenes/Coins";
import { Friends } from "./scenes/Friends";
import { Savings } from "./scenes/Savings";
import { Cta } from "./scenes/Cta";

export const SCENE_COMPONENTS: Record<SceneId, React.FC> = {
  hook: Hook,
  intro: Intro,
  step1: Step1,
  step2: Step2,
  step3: Step3,
  coins: Coins,
  friends: Friends,
  savings: Savings,
  cta: Cta,
};

const RAMP = 8;
const MUSIC_LOUD = 0.34;
const MUSIC_DUCKED = 0.11;

/** Music sits lower while the narrator speaks and swells in the gaps. */
const musicVolume = (frame: number) => {
  const ranges = voRanges();
  let duck = 0;
  for (const [a, b] of ranges) {
    duck = Math.max(
      duck,
      interpolate(frame, [a - RAMP, a, b, b + RAMP], [0, 1, 1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      }),
    );
  }
  return MUSIC_LOUD + (MUSIC_DUCKED - MUSIC_LOUD) * duck;
};

export const Promo: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: C.bg }}>
    <TransitionSeries>
      {SCENES.flatMap(({ id, extra }, i) => {
        const Scene = SCENE_COMPONENTS[id];
        const items = [
          <TransitionSeries.Sequence key={id} name={id} durationInFrames={sceneFrames(id, extra)}>
            <Scene />
          </TransitionSeries.Sequence>,
        ];
        if (i < SCENES.length - 1) {
          items.push(
            <TransitionSeries.Transition
              key={`${id}-t`}
              presentation={i % 3 === 1 ? fade() : slide({ direction: "from-bottom" })}
              timing={linearTiming({ durationInFrames: TRANSITION })}
            />,
          );
        }
        return items;
      })}
    </TransitionSeries>
    <Audio src={staticFile("music.mp3")} volume={musicVolume} />
  </AbsoluteFill>
);
