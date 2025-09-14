import React from 'react';
import type { CompositionBlueprint } from "~/video-compositions/BlueprintTypes";
import { ScrollArea, ScrollBar } from "~/components/ui/scroll-area";
import { Button } from "~/components/ui/button";
import { Scissors, Trash2 } from "lucide-react";
import type { PlayerRef } from "@remotion/player";

export interface TimelineViewProps {
  blueprint: CompositionBlueprint;
  className?: string;
  playerRef?: React.RefObject<PlayerRef | null>;
  currentFrame?: number;
  fps?: number;
  onFrameUpdate?: (frame: number) => void;
  onDropMedia?: (mediaItem: any, trackIndex: number, timeInSeconds: number) => void;
  onMoveClip?: (clipId: string, newTrackIndex: number, newStartTime: number) => void;
  onSplitClip?: (clipId: string, splitTimeInSeconds: number) => void;
  onDeleteClip?: (clipId: string) => void;
}

// Fresh component name to avoid any stale Vite graph node collisions.
export default function TimelineView({ 
  blueprint, 
  className = "", 
  playerRef, 
  currentFrame = 0, 
  fps = 30,
  onFrameUpdate,
  onDropMedia,
  onMoveClip,
  onSplitClip,
  onDeleteClip
}: TimelineViewProps) {
  const [zoomLevel, setZoomLevel] = React.useState(60); // pixels per second
  const [isDragging, setIsDragging] = React.useState(false);
  const [selectedClipId, setSelectedClipId] = React.useState<string | null>(null);
  const [draggingClip, setDraggingClip] = React.useState<{
    clipId: string;
    trackIndex: number;
    offsetX: number;
    originalStartTime: number;
  } | null>(null);
  const [dragPreview, setDragPreview] = React.useState<{
    trackIndex: number;
    startTime: number;
    duration: number;
    name: string;
    isClipMove?: boolean; // Flag to distinguish clip moves from media drops
  } | null>(null);
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

  // Handler for splitting selected clip at current playhead position
  const handleSplitSelectedClip = () => {
    if (!selectedClipId || !onSplitClip || !playerRef?.current) return;
    
    const currentTimeInSeconds = currentFrame / fps;
    onSplitClip(selectedClipId, currentTimeInSeconds);
  };

  // Handler for deleting selected clip
  const handleDeleteSelectedClip = () => {
    if (!selectedClipId || !onDeleteClip) return;
    
    onDeleteClip(selectedClipId);
    setSelectedClipId(null); // Clear selection after deletion
  };

    // Slider styling for zoom control
  React.useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      .slider::-webkit-slider-thumb {
        appearance: none;
        height: 10px;
        width: 10px;
        border-radius: 50%;
        background: hsl(var(--primary));
        cursor: pointer;
        border: 2px solid hsl(var(--background));
        box-shadow: 0 0 2px rgba(0, 0, 0, 0.2);
      }
      .slider::-webkit-slider-track {
        width: 100%;
        height: 2px;
        cursor: pointer;
        background: hsl(var(--border));
        border-radius: 1px;
      }
    `;
    document.head.appendChild(style);
    
    // Clean up drag preview when dragging ends
    const handleDragEnd = () => {
      setDragPreview(null);
      // Clean up global drag item
      delete (window as any).__draggedMediaItem;
    };
    
    document.addEventListener('dragend', handleDragEnd);
    
    return () => {
      document.head.removeChild(style);
      document.removeEventListener('dragend', handleDragEnd);
    };
  }, []);

  return (
    <div className={`bg-background border border-border rounded-lg p-4 ${className}`}>
      {/* Timeline Toolbar */}
      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-border">
        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="sm"
            onClick={handleSplitSelectedClip}
            disabled={!selectedClipId}
            className="flex items-center gap-1"
          >
            <Scissors className="w-3 h-3" />
            Split Clip
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleDeleteSelectedClip}
            disabled={!selectedClipId}
            className="flex items-center gap-1"
          >
            <Trash2 className="w-3 h-3" />
            Delete Clip
          </Button>
        </div>
        {selectedClipId && (
          <div className="text-xs text-muted-foreground">
            Selected: {selectedClipId.split('-').pop()}
          </div>
        )}
      </div>
      
      <div className="relative border border-border rounded overflow-hidden" style={{ height: 'calc(100% - 64px)' }}>
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
                // Deselect clip if clicking on empty timeline
                setSelectedClipId(null);
                
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
                      
                      const rect = e.currentTarget.getBoundingClientRect();
                      const dropX = e.clientX - rect.left;
                      const timeInSeconds = Math.max(0, dropX / pixelsPerSecond);
                      
                      // Check if we're dragging a clip (internal move) - similar to media bin approach
                      const draggedClip = (window as any).__draggedClip;
                      const draggedMediaItem = (window as any).__draggedMediaItem;
                      
                      console.log('DragOver - draggedClip:', draggedClip, 'draggedMediaItem:', draggedMediaItem);
                      
                      if (draggedClip) {
                        // Handle clip movement preview (blue)
                        const duration = draggedClip.endTimeInSeconds - draggedClip.startTimeInSeconds;
                        console.log('Setting blue preview for clip move:', {
                          trackIndex,
                          startTime: timeInSeconds,
                          duration,
                          name: draggedClip.name,
                          isClipMove: true
                        });
                        setDragPreview({
                          trackIndex,
                          startTime: timeInSeconds,
                          duration,
                          name: draggedClip.name,
                          isClipMove: true
                        });
                      } else if (draggedMediaItem) {
                        // Handle media item drop preview (gray)
                        const duration = draggedMediaItem.mediaType === 'image' ? 3 : (draggedMediaItem.durationInSeconds || 3);
                        console.log('Setting gray preview for media drop:', {
                          trackIndex,
                          startTime: timeInSeconds,
                          duration,
                          name: draggedMediaItem.name || 'Media Item',
                          isClipMove: false
                        });
                        
                        setDragPreview({
                          trackIndex,
                          startTime: timeInSeconds,
                          duration,
                          name: draggedMediaItem.name || 'Media Item',
                          isClipMove: false
                        });
                      }
                    }}
                    onDragLeave={(e) => {
                      e.currentTarget.classList.remove('bg-accent/20');
                      setDragPreview(null);
                    }}
                    onDrop={(e) => {
                      e.preventDefault();
                      e.currentTarget.classList.remove('bg-accent/20');
                      setDragPreview(null);
                      
                      const rect = e.currentTarget.getBoundingClientRect();
                      const dropX = e.clientX - rect.left;
                      const timeInSeconds = Math.max(0, dropX / pixelsPerSecond);
                      
                      // Check if we're dropping a clip (internal move)
                      const clipId = e.dataTransfer.getData('text/plain');
                      if (clipId && onMoveClip) {
                        console.log(`Moving clip ${clipId} to track ${trackIndex + 1} at ${timeInSeconds.toFixed(2)}s`);
                        onMoveClip(clipId, trackIndex, timeInSeconds);
                        setDraggingClip(null);
                        // Clean up the global clip data
                        (window as any).__draggedClip = null;
                        return;
                      }
                      
                      // Otherwise, handle media item drop
                      if (onDropMedia) {
                        try {
                          const mediaItem = JSON.parse(e.dataTransfer.getData("application/json"));
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
                          className={`absolute top-2 h-12 ${colorClass} rounded shadow-sm border-2 flex items-center px-2 select-none cursor-grab active:cursor-grabbing transition-all ${
                            selectedClipId === id ? 'border-yellow-400 shadow-lg' : 'border-background'
                          }`}
                          style={{ left, width }}
                          draggable={true}
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedClipId(selectedClipId === id ? null : id);
                          }}
                          onMouseDown={(e) => {
                            e.stopPropagation();
                            const rect = e.currentTarget.getBoundingClientRect();
                            const offsetX = e.clientX - rect.left;
                            setDraggingClip({
                              clipId: id,
                              trackIndex,
                              offsetX,
                              originalStartTime: clip.startTimeInSeconds
                            });
                          }}
                          onDragStart={(e) => {
                            e.dataTransfer.effectAllowed = 'move';
                            e.dataTransfer.setData('text/plain', id);
                            e.dataTransfer.setData('application/x-clip-id', id); // Alternative data type
                            console.log('Clip drag started:', id);
                            
                            // Store the dragged clip globally like media items do
                            const draggedClip = track.clips.find(clip => clip.id === id);
                            if (draggedClip) {
                              (window as any).__draggedClip = {
                                ...draggedClip,
                                name: id.split('-').pop() || 'Clip'
                              };
                            }
                            
                            // Create an invisible drag image to remove the overlay
                            const dragImage = document.createElement('div');
                            dragImage.style.cssText = `
                              position: absolute;
                              top: -1000px;
                              left: -1000px;
                              width: 1px;
                              height: 1px;
                              background: transparent;
                              pointer-events: none;
                            `;
                            document.body.appendChild(dragImage);
                            e.dataTransfer.setDragImage(dragImage, 0, 0);
                            setTimeout(() => document.body.removeChild(dragImage), 0);
                          }}
                        >
                          <span className="text-xs text-white dark:text-gray-100 font-medium truncate select-none pointer-events-none">
                            {id.split('-').pop() || 'Clip'}
                          </span>
                        </div>
                      );
                    })}
                    
                    {/* Drag Preview */}
                    {dragPreview && dragPreview.trackIndex === trackIndex && (
                      <div
                        className={`absolute top-2 h-12 border-2 border-dashed rounded flex items-center px-2 select-none pointer-events-none ${
                          dragPreview.isClipMove 
                            ? 'bg-blue-400/50 border-blue-300' 
                            : 'bg-gray-400/50 border-gray-300'
                        }`}
                        style={{ 
                          left: dragPreview.startTime * pixelsPerSecond,
                          width: Math.max(dragPreview.duration * pixelsPerSecond, 20)
                        }}
                      >
                        <span className={`text-xs font-medium truncate select-none ${
                          dragPreview.isClipMove 
                            ? 'text-blue-700 dark:text-blue-300'
                            : 'text-gray-600 dark:text-gray-300'
                        }`}>
                          {dragPreview.name}
                        </span>
                      </div>
                    )}
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
