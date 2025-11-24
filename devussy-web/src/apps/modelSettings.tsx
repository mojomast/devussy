import React from "react";
import type { AppDefinition } from "./appTypes";
import { Settings } from "lucide-react";
import {
  ModelSettings,
  ModelConfigs,
  PipelineStage,
} from "@/components/pipeline/ModelSettings";

interface ModelSettingsWindowProps {
  configs: ModelConfigs;
  onConfigsChange: (configs: ModelConfigs) => void;
  activeStage?: PipelineStage;
}

const ModelSettingsWindow: React.FC<ModelSettingsWindowProps> = ({
  configs,
  onConfigsChange,
  activeStage,
}) => {
  return (
    <ModelSettings
      configs={configs}
      onConfigsChange={onConfigsChange}
      activeStage={activeStage}
      isWindowMode={true}
    />
  );
};

const ModelSettingsApp: AppDefinition = {
  id: "model-settings",
  name: "AI Model Settings",
  icon: <Settings className="w-4 h-4" />,
  defaultSize: { width: 500, height: 650 },
  startMenuCategory: "Settings",
  singleInstance: true,
  component: ModelSettingsWindow,
};

export default ModelSettingsApp;
