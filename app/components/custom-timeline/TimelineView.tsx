import React from 'react';
import type { CompositionBlueprint } from "~/video-compositions/BlueprintTypes";
import { ScrollArea, ScrollBar } from "~/components/ui/scroll-area";

export interface TimelineViewProps {
  blueprint: CompositionBlueprint;
  className?: string;
}

// Fresh component name to avoid any stale Vite graph node collisions.
export default function TimelineView({ blueprint, className = "" }: TimelineViewProps) {
  const [zoomLevel, setZoomLevel] = React.useState(60); // pixels per second

  // Derive total timeline duration
  let maxEnd = 0;
  for (const track of blueprint) {
    for (const clip of track.clips) {
      if (clip.endTimeInSeconds > maxEnd) maxEnd = clip.endTimeInSeconds;
    }
  }
  const totalDuration = Math.max(maxEnd, 10);

  const pixelsPerSecond = zoomLevel;
  const timelineWidth = totalDuration * pixelsPerSecond;

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
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-foreground">Timeline Preview</h3>
        <p className="text-sm text-muted-foreground">
          {blueprint.length} tracks • {totalDuration.toFixed(1)}s duration
        </p>
      </div>
      <div className="relative border border-border rounded overflow-hidden" style={{ height: 'calc(100% - 80px)' }}>
        <ScrollArea className="h-full w-full">
          <div style={{ width: Math.max(timelineWidth + 100, 800), minHeight: '100%' }} className="relative">
              <div className="h-8 bg-muted border-b border-border relative flex-shrink-0 sticky top-0 z-10">
                {Array.from({ length: Math.ceil(totalDuration) + 1 }, (_, i) => (
                  <div
                    key={i}
                    className="absolute top-0 h-full border-l border-border flex items-center"
                    style={{ left: i * pixelsPerSecond + 50 }}
                  >
                    <span className="text-xs text-muted-foreground ml-1">{i}s</span>
                  </div>
                ))}
              </div>
              <div className="bg-background">
                {blueprint.map((track, trackIndex) => (
                  <div key={trackIndex} className="h-16 border-b border-border relative flex items-center">
                    <div className="w-12 h-full bg-muted border-r border-border flex items-center justify-center flex-shrink-0">
                      <span className="text-xs font-medium text-muted-foreground">T{trackIndex + 1}</span>
                    </div>
                    <div className="relative flex-1">
                      {track.clips.map((clip, clipIndex) => {
                        const left = clip.startTimeInSeconds * pixelsPerSecond + 50;
                        const width = Math.max((clip.endTimeInSeconds - clip.startTimeInSeconds) * pixelsPerSecond, 20);
                        const id = clip.id || `clip-${trackIndex}-${clipIndex}`;
                        const colorClass = id.includes('video')
                          ? 'bg-blue-500/80 dark:bg-blue-600/80'
                          : id.includes('image')
                          ? 'bg-green-500/80 dark:bg-green-600/80'
                          : id.includes('text')
                          ? 'bg-purple-500/80 dark:bg-purple-600/80'
                          : 'bg-primary/60 dark:bg-primary/70';
                        return (
                          <div
                            key={clipIndex}
                            className={`absolute top-2 h-12 ${colorClass} rounded shadow-sm border border-background flex items-center px-2`}
                            style={{ left, width }}
                          >
                            <span className="text-xs text-white dark:text-gray-100 font-medium truncate">
                              {id.split('-').pop() || 'Clip'}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          <ScrollBar orientation="horizontal" />
        </ScrollArea>
      </div>
      <div className="mt-3 flex items-center justify-between">
        <div className="flex gap-4 text-xs text-muted-foreground">
          <span>Total Clips: {blueprint.reduce((s, t) => s + t.clips.length, 0)}</span>
          <span>Tracks: {blueprint.length}</span>
          <span>Duration: {totalDuration.toFixed(1)}s</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Zoom:</span>
          <input
            type="range"
            min="20"
            max="200"
            step="10"
            value={zoomLevel}
            onChange={(e) => setZoomLevel(Number(e.target.value))}
            className="w-20 h-1 bg-border rounded-sm appearance-none cursor-pointer slider"
          />
          <span className="text-xs text-muted-foreground w-8">{Math.round((zoomLevel / 60) * 100)}%</span>
        </div>
      </div>
    </div>
  );
}
