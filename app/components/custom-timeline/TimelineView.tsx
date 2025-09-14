import React from 'react';
import type { CompositionBlueprint } from "~/video-compositions/BlueprintTypes";
import { ScrollArea, ScrollBar } from "~/components/ui/scroll-area";
import type { PlayerRef } from "@remotion/player";

export interface TimelineViewProps {
  blueprint: CompositionBlueprint;
  className?: string;
  playerRef?: React.RefObject<PlayerRef | null>;
  currentFrame?: number;
  fps?: number;
  onFrameUpdate?: (frame: number) => void;
  onDropMedia?: (mediaItem: any, trackIndex: number, timeInSeconds: number) => void;
}

// Fresh component name to avoid any stale Vite graph node collisions.
export default function TimelineView({ 
  blueprint, 
  className = "", 
  playerRef, 
  currentFrame = 0, 
  fps = 30,
  onFrameUpdate,
  onDropMedia
}: TimelineViewProps) {
  const [zoomLevel, setZoomLevel] = React.useState(60); // pixels per second
  const [isDragging, setIsDragging] = React.useState(false);
  const timelineRef = React.useRef<HTMLDivElement>(null);

  // Derive total timeline duration
  let maxEnd = 0;
  for (const track of blueprint) {
    for (const clip of track.clips) {
      if (clip.endTimeInSeconds > maxEnd) maxEnd = clip.endTimeInSeconds;
    }
  }
  const totalDuration = Math.max(maxEnd, 10);

  const pixelsPerSecond = zoomLevel;
  // Extend timeline much further than content for infinite ruler effect
  // Scale the extension based on zoom level to maintain performance
  const extensionMultiplier = Math.max(3, Math.min(10, 1000 / pixelsPerSecond)); // More extension at higher zoom
  const extendedDuration = Math.max(totalDuration * extensionMultiplier, 60); // At least 1 minute
  const timelineWidth = extendedDuration * pixelsPerSecond;

  // Slider styling for zoom control
  React.useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      .slider::-webkit-slider-thumb {
        appearance: none;
        height: 10px;
        width: 10px;
        border-radius: 2px;
        background: hsl(var(--foreground));
        cursor: pointer;
        border: none;
      }
      .slider::-moz-range-thumb {
        height: 10px;
        width: 10px;
        border-radius: 2px;
        background: hsl(var(--foreground));
        cursor: pointer;
        border: none;
      }
    `;
    document.head.appendChild(style);
    return () => {
      if (document.head.contains(style)) {
        document.head.removeChild(style);
      }
    };
  }, []);

  return (
    <div className={`bg-background border border-border rounded-lg p-4 ${className}`}>
      <div className="relative border border-border rounded overflow-hidden" style={{ height: 'calc(100% - 16px)' }}>
        <ScrollArea className="h-full w-full">
          <div className="flex w-full">
            {/* Track labels column */}
            <div className="w-12 flex-shrink-0 bg-muted border-r border-border flex flex-col">
              <div className="h-8 border-b border-border" />
              {blueprint.map((track, trackIndex) => (
                <div key={trackIndex} className="h-16 border-b border-border flex items-center justify-center select-none">
                  <span className="text-xs font-medium text-muted-foreground select-none">T{trackIndex + 1}</span>
                </div>
              ))}
            </div>
            {/* Timeline content area */}
            <div
              ref={timelineRef}
              className="relative flex-1 cursor-pointer select-none"
              style={{ width: Math.max(timelineWidth, 800), minHeight: '100%' }}
              onMouseDown={(e) => {
                setIsDragging(true);
                if (playerRef?.current) {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const clickX = e.clientX - rect.left;
                  const clickTime = clickX / pixelsPerSecond;
                  const clickFrame = Math.max(0, Math.round(clickTime * fps));
                  playerRef.current.seekTo(clickFrame);
                  onFrameUpdate?.(clickFrame);
                }
              }}
              onMouseMove={(e) => {
                if (isDragging && playerRef?.current) {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const clickX = e.clientX - rect.left;
                  const clickTime = clickX / pixelsPerSecond;
                  const clickFrame = Math.max(0, Math.round(clickTime * fps));
                  playerRef.current.seekTo(clickFrame);
                  onFrameUpdate?.(clickFrame);
                }
              }}
              onMouseUp={() => setIsDragging(false)}
              onMouseLeave={() => setIsDragging(false)}
            >
              {/* Playhead/Scrubber */}
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-30 pointer-events-none"
                style={{ left: (currentFrame / fps) * pixelsPerSecond }}
              >
                <div className="absolute -top-1 -left-1.5 w-3 h-2 bg-red-500 rounded-sm"></div>
              </div>
              
              {/* Ruler */}
              <div className="h-8 bg-muted border-b border-border relative flex-shrink-0 sticky top-0 z-10 select-none">
                {Array.from({ length: Math.ceil(extendedDuration) + 1 }, (_, i) => (
                  <div
                    key={i}
                    className="absolute top-0 h-full border-l border-border flex items-center select-none"
                    style={{ left: i * pixelsPerSecond }}
                  >
                    <span className="text-xs text-muted-foreground ml-1 select-none">{i}s</span>
                  </div>
                ))}
              </div>
              {/* Tracks */}
              <div className="bg-background">
                {blueprint.map((track, trackIndex) => (
                  <div 
                    key={trackIndex} 
                    className="h-16 border-b border-border relative select-none"
                    onDragOver={(e) => {
                      e.preventDefault();
                      e.currentTarget.classList.add('bg-accent/20');
                    }}
                    onDragLeave={(e) => {
                      e.currentTarget.classList.remove('bg-accent/20');
                    }}
                    onDrop={(e) => {
                      e.preventDefault();
                      e.currentTarget.classList.remove('bg-accent/20');
                      
                      if (onDropMedia) {
                        try {
                          const mediaItem = JSON.parse(e.dataTransfer.getData("application/json"));
                          const rect = e.currentTarget.getBoundingClientRect();
                          const dropX = e.clientX - rect.left;
                          const timeInSeconds = Math.max(0, dropX / pixelsPerSecond);
                          
                          console.log(`Dropped ${mediaItem.name} on track ${trackIndex + 1} at ${timeInSeconds.toFixed(2)}s`);
                          onDropMedia(mediaItem, trackIndex, timeInSeconds);
                        } catch (error) {
                          console.error("Failed to parse dropped data:", error);
                        }
                      }
                    }}
                  >
                    {track.clips.map((clip, clipIndex) => {
                      const left = clip.startTimeInSeconds * pixelsPerSecond;
                      const width = Math.max((clip.endTimeInSeconds - clip.startTimeInSeconds) * pixelsPerSecond, 20);
                      const id = clip.id || `clip-${trackIndex}-${clipIndex}`;
                      
                      // Alternate colors for adjacent clips on the same track
                      const colors = [
                        'bg-blue-500/80 dark:bg-blue-600/80',
                        'bg-green-500/80 dark:bg-green-600/80',
                        'bg-purple-500/80 dark:bg-purple-600/80',
                        'bg-orange-500/80 dark:bg-orange-600/80',
                        'bg-pink-500/80 dark:bg-pink-600/80',
                        'bg-teal-500/80 dark:bg-teal-600/80'
                      ];
                      const colorClass = colors[clipIndex % colors.length];
                      
                      return (
                        <div
                          key={clipIndex}
                          className={`absolute top-2 h-12 ${colorClass} rounded shadow-sm border border-background flex items-center px-2 select-none`}
                          style={{ left, width }}
                        >
                          <span className="text-xs text-white dark:text-gray-100 font-medium truncate select-none">
                            {id.split('-').pop() || 'Clip'}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          </div>
          <ScrollBar orientation="horizontal" />
        </ScrollArea>
      </div>
      <div className="mt-3 flex items-center justify-between select-none">
        <div className="flex gap-4 text-xs text-muted-foreground select-none">
          <span className="select-none">Total Clips: {blueprint.reduce((s, t) => s + t.clips.length, 0)}</span>
          <span className="select-none">Tracks: {blueprint.length}</span>
          <span className="select-none">Duration: {totalDuration.toFixed(1)}s</span>
        </div>
        <div className="flex items-center gap-2 select-none">
          <span className="text-xs text-muted-foreground select-none">Zoom:</span>
          <input
            type="range"
            min="20"
            max="200"
            step="10"
            value={zoomLevel}
            onChange={(e) => setZoomLevel(Number(e.target.value))}
            className="w-20 h-1 bg-border rounded-sm appearance-none cursor-pointer slider"
          />
          <span className="text-xs text-muted-foreground w-8 select-none">{Math.round((zoomLevel / 60) * 100)}%</span>
        </div>
      </div>
    </div>
  );
}
