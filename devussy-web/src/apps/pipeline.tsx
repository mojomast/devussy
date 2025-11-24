import React from "react";
import type { AppDefinition } from "./appTypes";
import { Layers } from "lucide-react";

const PipelineRoot: React.FC<any> = () => null;

const PipelineApp: AppDefinition = {
  id: "pipeline",
  name: "Devussy Pipeline",
  icon: <Layers className="w-4 h-4" />,
  defaultSize: { width: 900, height: 750 },
  startMenuCategory: "Devussy",
  component: PipelineRoot,
};

export default PipelineApp;
