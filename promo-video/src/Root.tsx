import React from "react";
import { Composition, Folder } from "remotion";
import { Promo, SCENE_COMPONENTS } from "./Promo";
import { FPS, sceneFrames, SCENES, TOTAL_FRAMES } from "./theme";

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="CoffeePassPromo"
      component={Promo}
      durationInFrames={TOTAL_FRAMES}
      fps={FPS}
      width={1080}
      height={1920}
    />
    <Folder name="Scenes">
      {SCENES.map(({ id, extra }) => (
        <Composition
          key={id}
          id={`Scene-${id}`}
          component={SCENE_COMPONENTS[id]}
          durationInFrames={sceneFrames(id, extra)}
          fps={FPS}
          width={1080}
          height={1920}
        />
      ))}
    </Folder>
  </>
);
