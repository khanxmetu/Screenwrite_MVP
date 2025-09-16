import React from 'react';
import type { CompositionBlueprint } from "~/video-compositions/BlueprintTypes";

interface SimpleTimelineProps {
  blueprint: CompositionBlueprint;
  className?: string;
}

function SimpleTimeline({ 
  blueprint, 
  className = "" 
}: SimpleTimelineProps) {
  // Calculate total duration from all tracks
  const getTotalDuration = () => {
    let maxEnd = 0;
    blueprint.forEach(track => {
      track.clips.forEach(clip => {
        const clipEnd = clip.endTimeInSeconds;
        if (clipEnd > maxEnd) maxEnd = clipEnd;
      });
    });
    return Math.max(maxEnd, 10); // Minimum 10 seconds
  };

  const totalDuration = getTotalDuration();
  const pixelsPerSecond = 60; // 60px per second
  const timelineWidth = totalDuration * pixelsPerSecond;

  return (
    <div className={`bg-background border border-border rounded-lg p-4 ${className}`}>
      {/* Header */}
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-foreground">Timeline Preview</h3>
        <p className="text-sm text-muted-foreground">
          {blueprint.length} tracks • {totalDuration.toFixed(1)}s duration
        </p>
      </div>

      {/* Timeline Container */}
      <div className="relative border border-border rounded overflow-hidden" style={{ height: 'calc(100% - 80px)' }}>
        <div className="h-full flex flex-col">
          {/* Single Scrollable Container for Both Ruler and Tracks */}
          <div className="flex-1 overflow-auto">
            <div style={{ width: Math.max(timelineWidth + 100, 800) }}>
              {/* Time Ruler */}
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

              {/* Tracks */}
              <div className="bg-background">
                {blueprint.map((track, trackIndex) => (
                  <div 
                    key={trackIndex}
                    className="h-16 border-b border-border relative flex items-center"
                  >
                    {/* Track Label */}
                    <div className="w-12 h-full bg-muted border-r border-border flex items-center justify-center flex-shrink-0">
                      <span className="text-xs font-medium text-muted-foreground">T{trackIndex + 1}</span>
                    </div>

                    {/* Track Content */}
                    <div className="relative flex-1">
                      {track.clips.map((clip, clipIndex) => {
                        const clipStart = clip.startTimeInSeconds * pixelsPerSecond;
                        const clipWidth = (clip.endTimeInSeconds - clip.startTimeInSeconds) * pixelsPerSecond;
                        
                        // Theme-aware colors based on clip type or id
                        const getClipColor = (clipId: string) => {
                          if (clipId.includes('video')) return 'bg-blue-500/80 dark:bg-blue-600/80';
                          if (clipId.includes('image')) return 'bg-green-500/80 dark:bg-green-600/80';  
                          if (clipId.includes('text')) return 'bg-purple-500/80 dark:bg-purple-600/80';
                          return 'bg-primary/60 dark:bg-primary/70';
                        };

                        return (
                          <div
                            key={clipIndex}
                            className={`absolute top-2 h-12 ${getClipColor(clip.id)} rounded shadow-sm border border-background flex items-center px-2`}
                            style={{ 
                              left: clipStart + 50, 
                              width: Math.max(clipWidth, 20) // Minimum width for visibility
                            }}
                          >
                            <span className="text-xs text-white dark:text-gray-100 font-medium truncate">
                              {clip.id.split('-').pop() || 'Clip'}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="mt-3 flex gap-4 text-xs text-muted-foreground">
        <span>Total Clips: {blueprint.reduce((sum, track) => sum + track.clips.length, 0)}</span>
        <span>Tracks: {blueprint.length}</span>
        <span>Duration: {totalDuration.toFixed(1)}s</span>
      </div>
    </div>
  );
}

export default SimpleTimeline;
