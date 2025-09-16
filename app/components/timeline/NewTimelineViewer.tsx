import React from 'react';
import { Timeline } from '@xzdarcy/react-timeline-editor';
import type { CompositionBlueprint } from "../../video-compositions/BlueprintTypes";
import { blueprintToTimelineData, getBlueprintDurationInSeconds } from './adapters';

interface TimelineViewerProps {
  blueprint: CompositionBlueprint;
  className?: string;
}

export const TimelineViewer: React.FC<TimelineViewerProps> = ({ 
  blueprint, 
  className = "" 
}) => {
  const { editorData, effects } = blueprintToTimelineData(blueprint);
  const duration = getBlueprintDurationInSeconds(blueprint);

  return (
    <div className={`timeline-container ${className}`}>
      <Timeline
        editorData={editorData}
        effects={effects}
        scale={1}
        scaleWidth={100}
        startLeft={20}
        minScaleCount={Math.max(20, Math.ceil(duration))}
        maxScaleCount={Math.max(60, Math.ceil(duration * 2))}
        scaleSplitCount={10}
        rowHeight={40}
        gridSnap={true}
        dragLine={false}
        hideCursor={false}
        disableDrag={true} // Read-only mode
        autoReRender={true}
        style={{
          width: '100%',
          height: '200px',
          border: '1px solid #e2e8f0',
          borderRadius: '6px',
          overflow: 'hidden'
        }}
      />
    </div>
  );
};
