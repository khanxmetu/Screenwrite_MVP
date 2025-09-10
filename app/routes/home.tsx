import React, { useRef, useEffect, useCallback, useState } from "react";
import type { PlayerRef } from "@remotion/player";
import * as Remotion from "remotion";
import { TransitionSeries, linearTiming, springTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { wipe } from "@remotion/transitions/wipe";
import { flip } from "@remotion/transitions/flip";
import { iris } from "@remotion/transitions/iris";
import { none } from "@remotion/transitions/none";
import { Animated, Move, Scale, Fade as AnimatedFade, Rotate } from "remotion-animated";
import {
  Moon,
  Sun,
  Upload,
  ChevronLeft,
} from "lucide-react";

import { useTheme } from "next-themes";

// Components
import LeftPanel from "~/components/editor/LeftPanel";
import { StandaloneVideoPlayer } from "~/video-compositions/StandalonePreview";
import { DynamicVideoPlayer } from "~/video-compositions/DynamicComposition";
import { RenderStatus } from "~/components/timeline/RenderStatus";
import { Button } from "~/components/ui/button";
import { Badge } from "~/components/ui/badge";
import { Separator } from "~/components/ui/separator";
import { Switch } from "~/components/ui/switch";
import { Label } from "~/components/ui/label";
import { Input } from "~/components/ui/input";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "~/components/ui/resizable";
import { toast } from "sonner";

// Hooks
import { useMediaBin } from "~/hooks/useMediaBin";
import { useRenderer } from "~/hooks/useRenderer";
import { useStandalonePreview } from "~/hooks/useStandalonePreview";

// Types and constants
import { type Transition, type MediaBinItem } from "~/components/timeline/types";
import { useNavigate } from "react-router";
import { ChatBox } from "~/components/chat/ChatBox";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

export default function TimelineEditor() {
  const containerRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<PlayerRef>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { theme, setTheme } = useTheme();

  const navigate = useNavigate();

  const [width, setWidth] = useState<number>(1920);
  const [height, setHeight] = useState<number>(1080);
  const [isAutoSize, setIsAutoSize] = useState<boolean>(false);
  const [isChatMinimized, setIsChatMinimized] = useState<boolean>(true);

  // Video playback state
  const [durationInFrames, setDurationInFrames] = useState<number>(1); // Minimal duration - gets updated by AI

  // Sample code toggle state
  const [useSampleCode, setUseSampleCode] = useState<boolean>(false);

  const [chatMessages, setChatMessages] = useState<Message[]>([]);
  const [mounted, setMounted] = useState(false)

  // video player media selection state
  const [selectedItem, setSelectedItem] = useState<string | null>(null);

  // VERBATIM copy of DynamicComposition execution logic for validation
  const validateTsxCode = useCallback((tsxCode: string): boolean => {
    try {
      console.log('🧪 Validating AI-generated code:', tsxCode.slice(0, 100) + '...');

      // Helper function to convert seconds to frames (same as DynamicComposition)
      const inSeconds = (seconds: number): number => {
        return Math.round(seconds * 30); // 30 FPS
      };

      // Ease object with common easing functions (same as DynamicComposition)
      const Ease = {
        Linear: (t: number) => t,
        QuadraticIn: (t: number) => t * t,
        QuadraticOut: (t: number) => 1 - (1 - t) * (1 - t),
        QuadraticInOut: (t: number) => t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2,
        CubicIn: (t: number) => t * t * t,
        CubicOut: (t: number) => 1 - Math.pow(1 - t, 3),
        CubicInOut: (t: number) => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
        QuarticIn: (t: number) => t * t * t * t,
        QuarticOut: (t: number) => 1 - Math.pow(1 - t, 4),
        QuarticInOut: (t: number) => t < 0.5 ? 8 * t * t * t * t : 1 - Math.pow(-2 * t + 2, 4) / 2,
        QuinticIn: (t: number) => t * t * t * t * t,
        QuinticOut: (t: number) => 1 - Math.pow(1 - t, 5),
        QuinticInOut: (t: number) => t < 0.5 ? 16 * t * t * t * t * t : 1 - Math.pow(-2 * t + 2, 5) / 2,
        SinusoidalIn: (t: number) => 1 - Math.cos((t * Math.PI) / 2),
        SinusoidalOut: (t: number) => Math.sin((t * Math.PI) / 2),
        SinusoidalInOut: (t: number) => -(Math.cos(Math.PI * t) - 1) / 2,
        CircularIn: (t: number) => 1 - Math.sqrt(1 - Math.pow(t, 2)),
        CircularOut: (t: number) => Math.sqrt(1 - Math.pow(t - 1, 2)),
        CircularInOut: (t: number) => t < 0.5 ? (1 - Math.sqrt(1 - Math.pow(2 * t, 2))) / 2 : (Math.sqrt(1 - Math.pow(-2 * t + 2, 2)) + 1) / 2,
        ExponentialIn: (t: number) => t === 0 ? 0 : Math.pow(2, 10 * (t - 1)),
        ExponentialOut: (t: number) => t === 1 ? 1 : 1 - Math.pow(2, -10 * t),
        ExponentialInOut: (t: number) => t === 0 ? 0 : t === 1 ? 1 : t < 0.5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2,
        BounceIn: (t: number) => 1 - Ease.BounceOut(1 - t),
        BounceOut: (t: number) => {
          const n1 = 7.5625;
          const d1 = 2.75;
          if (t < 1 / d1) return n1 * t * t;
          if (t < 2 / d1) return n1 * (t -= 1.5 / d1) * t + 0.75;
          if (t < 2.5 / d1) return n1 * (t -= 2.25 / d1) * t + 0.9375;
          return n1 * (t -= 2.625 / d1) * t + 0.984375;
        },
        BounceInOut: (t: number) => t < 0.5 ? (1 - Ease.BounceOut(1 - 2 * t)) / 2 : (1 + Ease.BounceOut(2 * t - 1)) / 2,
        Bezier: (x1: number, y1: number, x2: number, y2: number) => {
          // Simplified bezier function - for full implementation would need cubic-bezier
          return (t: number) => {
            // Linear interpolation approximation for simplicity
            return t < 0.5 ? 2 * t * t * (3 - 2 * t) : 1 - 2 * (1 - t) * (1 - t) * (3 - 2 * (1 - t));
          };
        }
      };

      // SIMPLIFIED VALIDATION - Match DynamicComposition exactly
      const executeCode = new Function(
        'React',
        'Animated', 
        'Move', 
        'Scale', 
        'Rotate', 
        'AnimatedFade',
        'inSeconds',
        'Ease',
        tsxCode
      );

      const generatedJSX = executeCode(
        React,
        Animated,
        Move,
        Scale,
        Rotate,
        AnimatedFade,
        inSeconds,
        Ease
      );

      console.log('✅ Validation passed');
      return true;
    } catch (error) {
      console.error('❌ Validation failed:', error);
      return false;
    }
  }, []);

  const {
    mediaBinItems,
    handleAddMediaToBin,
    handleAddTextToBin,
    contextMenu,
    handleContextMenu,
    handleDeleteFromContext,
    handleSplitAudioFromContext,
    handleCloseContextMenu
  } = useMediaBin(() => {}); // Empty function since we don't need timeline integration

  const { isRendering, renderStatus, handleRenderVideo } = useRenderer();

  // Standalone preview hook
  const {
    previewContent,
    generatedTsxCode,
    previewSettings,
    isGenerating,
    lastAiExplanation,
    generationError,
    addPreviewContent,
    removePreviewContent,
    updatePreviewContent,
    clearPreviewContent,
    generateAiContent,
    loadSampleContent,
    updatePreviewSettings,
    setGeneratedTsxCode,
    retryWithFix,
    clearError,
    handleExecutionError,
  } = useStandalonePreview(setDurationInFrames, validateTsxCode);

  // Wrapper function for AI composition generation with media library context
  // Function to explain composition changes
  const handleGenerateAiComposition = useCallback(async (userRequest: string, mediaBinItems: MediaBinItem[]): Promise<boolean> => {
    return await generateAiContent(userRequest, mediaBinItems);
  }, [generateAiContent]);

  // Store the last user request for error handling
  const [lastUserRequest, setLastUserRequest] = useState<string>("");

  // Wrapper for handling execution errors from DynamicComposition
  const handleVideoPlayerError = useCallback((error: Error, brokenCode: string) => {
    handleExecutionError(error, brokenCode, lastUserRequest);
  }, [handleExecutionError, lastUserRequest]);

  // Enhanced wrapper that tracks user requests
  const handleGenerateAiCompositionWithTracking = useCallback(async (userRequest: string, mediaBinItems: MediaBinItem[]): Promise<boolean> => {
    setLastUserRequest(userRequest); // Store for error handling
    return await generateAiContent(userRequest, mediaBinItems);
  }, [generateAiContent]);

  // Event handlers
  const handleAddMediaClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileInputChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        const fileArray = Array.from(files);
        let successCount = 0;
        let errorCount = 0;

        // Process files sequentially to avoid overwhelming the system
        for (const file of fileArray) {
          try {
            await handleAddMediaToBin(file);
            successCount++;
          } catch (error) {
            errorCount++;
            console.error(`Failed to add ${file.name}:`, error);
          }
        }

        if (successCount > 0 && errorCount > 0) {
          toast.warning(`Imported ${successCount} file${successCount > 1 ? 's' : ''}, ${errorCount} failed`);
        } else if (errorCount > 0) {
          toast.error(`Failed to import ${errorCount} file${errorCount > 1 ? 's' : ''}`);
        }

        e.target.value = "";
      }
    },
    [handleAddMediaToBin]
  );

  const handleAutoSizeChange = useCallback((auto: boolean) => {
    setIsAutoSize(auto);
  }, []);

  // Update duration when composition changes
  useEffect(() => {
    if (generatedTsxCode) {
      // For generated TSX, duration is now handled by AI response callback
      // Don't override the AI-determined duration here
    } else if (previewContent && previewContent.length > 0) {
      // Calculate duration from preview content
      const maxDuration = previewContent.reduce((max, item) => {
        return Math.max(max, item.duration || 3);
      }, 0);
      setDurationInFrames(Math.max(maxDuration * 30, 90)); // At least 3 seconds
    } else {
      setDurationInFrames(300); // Default 10 seconds
    }
  }, [previewContent]); // Removed generatedTsxCode dependency

  // Global spacebar play/pause functionality - like original
  useEffect(() => {
    const handleGlobalKeyPress = (event: KeyboardEvent) => {
      // Only handle spacebar when not focused on input elements
      if (event.code === "Space") {
        const target = event.target as HTMLElement;
        const isInputElement =
          target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.contentEditable === "true" ||
          target.isContentEditable;

        // If user is typing in an input field, don't interfere
        if (isInputElement) {
          return;
        }

        // Prevent spacebar from scrolling the page
        event.preventDefault();

        const player = playerRef.current;
        if (player) {
          if (player.isPlaying()) {
            player.pause();
          } else {
            player.play();
          }
        }
      }
    };

    // Add event listener to document for global capture
    document.addEventListener("keydown", handleGlobalKeyPress);

    return () => {
      document.removeEventListener("keydown", handleGlobalKeyPress);
    };
  }, []); // Empty dependency array since we're accessing playerRef.current directly


  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) return null;

  return (
    <div className="h-screen flex flex-col bg-background text-foreground" onPointerDown={(e: React.PointerEvent) => {
      if (e.button !== 0) {
        return;
      }
      setSelectedItem(null);
    }}>
      {/* Ultra-minimal Top Bar */}
      <header className="h-9 border-b border-border/50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 flex items-center justify-between px-3 shrink-0">
        <div className="flex items-center gap-3">
          <h1 className="text-sm font-medium tracking-tight">Screenwrite</h1>
        </div>

        <div className="flex items-center gap-1">
          {/* Theme Toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="h-7 w-7 p-0 hover:bg-muted"
          >
            {theme === "dark" ? (
              <Sun className="h-3.5 w-3.5" />
            ) : (
              <Moon className="h-3.5 w-3.5" />
            )}
          </Button>

          <Separator orientation="vertical" className="h-4 mx-1" />

          {/* Import/Export */}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleAddMediaClick}
            className="h-7 px-2 text-xs"
          >
            <Upload className="h-3 w-3 mr-1" />
            Import
          </Button>
        </div>
      </header>

      {/* Main content area with chat extending to bottom */}
      <ResizablePanelGroup direction="horizontal" className="flex-1">
        {/* Left section with media bin, video preview, and timeline */}
        <ResizablePanel defaultSize={isChatMinimized ? 100 : 80}>
          <ResizablePanelGroup direction="vertical">
            {/* Top section with media bin and video preview */}
            <ResizablePanel defaultSize={65} minSize={40}>
              <ResizablePanelGroup direction="horizontal">
                {/* Left Panel - Media Bin & Tools */}
                <ResizablePanel defaultSize={25} minSize={15} maxSize={40}>
                  <div className="h-full border-r border-border">
                    <LeftPanel
                      mediaBinItems={mediaBinItems}
                      onAddMedia={handleAddMediaToBin}
                      onAddText={handleAddTextToBin}
                      contextMenu={contextMenu}
                      handleContextMenu={handleContextMenu}
                      handleDeleteFromContext={handleDeleteFromContext}
                      handleSplitAudioFromContext={handleSplitAudioFromContext}
                      handleCloseContextMenu={handleCloseContextMenu}
                    />
                  </div>
                </ResizablePanel>

                <ResizableHandle withHandle />

                {/* Video Preview Area */}
                <ResizablePanel defaultSize={75}>
                  <div className="h-full flex flex-col bg-background">
                    {/* Compact Top Bar */}
                    <div className="h-8 border-b border-border/50 bg-muted/30 flex items-center justify-between px-3 shrink-0">
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        <span>Resolution:</span>
                        <div className="flex items-center gap-1">
                          <Input
                            type="number"
                            value={width}
                            onChange={(e) =>
                              setWidth(Number(e.target.value))
                            }
                            disabled={isAutoSize}
                            className="h-5 w-14 text-xs px-1 border-0 bg-muted/50"
                          />
                          <span>×</span>
                          <Input
                            type="number"
                            value={height}
                            onChange={(e) =>
                              setHeight(Number(e.target.value))
                            }
                            disabled={isAutoSize}
                            className="h-5 w-14 text-xs px-1 border-0 bg-muted/50"
                          />
                        </div>
                      </div>

                      <div className="flex items-center gap-1">
                        <div className="flex items-center gap-1">
                          <Switch
                            id="auto-size"
                            checked={isAutoSize}
                            onCheckedChange={handleAutoSizeChange}
                            className="scale-75"
                          />
                          <Label htmlFor="auto-size" className="text-xs">
                            Auto
                          </Label>
                        </div>

                        {/* Preview Settings */}
                        <div className="flex items-center gap-1 ml-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={clearPreviewContent}
                            className="h-5 px-2 text-xs"
                          >
                            Clear
                          </Button>
                          <Input
                            type="color"
                            value={previewSettings.backgroundColor}
                            onChange={(e) =>
                              updatePreviewSettings({ backgroundColor: e.target.value })
                            }
                            className="h-5 w-8 p-0 border-0"
                            title="Background Color"
                          />
                          
                          {/* Thinking Budget Controls */}
                          <div className="flex items-center gap-1">
                            <span className="text-xs text-muted-foreground">Synth:</span>
                            <Input
                              type="number"
                              value={previewSettings.synthThinkingBudget}
                              onChange={(e) => {
                                const value = parseInt(e.target.value);
                                // Allow 0 (no thinking), -1 (unlimited), or positive numbers
                                if (!isNaN(value)) {
                                  updatePreviewSettings({ synthThinkingBudget: value });
                                }
                              }}
                              className="h-5 w-16 px-1 text-xs"
                              title="Synth Thinking Budget (0=no thinking, -1=unlimited)"
                              step="100"
                            />
                            <span className="text-xs text-muted-foreground">Code:</span>
                            <Input
                              type="number"
                              value={previewSettings.codeGenThinkingBudget}
                              onChange={(e) => {
                                const value = parseInt(e.target.value);
                                // Allow 0 (no thinking), -1 (unlimited), or positive numbers
                                if (!isNaN(value)) {
                                  updatePreviewSettings({ codeGenThinkingBudget: value });
                                }
                              }}
                              className="h-5 w-16 px-1 text-xs"
                              title="Code Generation Thinking Budget (0=no thinking, -1=unlimited)"
                              step="100"
                            />
                          </div>
                        </div>

                        {/* Show chat toggle when minimized */}
                        {isChatMinimized && (
                          <>
                            <Separator
                              orientation="vertical"
                              className="h-4 mx-1"
                            />
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setIsChatMinimized(false)}
                              className="h-6 px-2 text-xs"
                              title="Show Chat"
                            >
                              <ChevronLeft className="h-3 w-3 mr-1" />
                              Chat
                            </Button>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Video Preview */}
                    <div
                      className={`flex-1 ${theme === "dark" ? "bg-zinc-900" : "bg-zinc-200/70"
                        } flex flex-col items-center justify-center p-3 border border-border/50 rounded-lg overflow-hidden shadow-2xl relative`}
                    >
                      {/* Sample Content Button */}
                      <div className="absolute top-2 right-2 flex items-center gap-2 z-10">
                        <Button
                          variant={useSampleCode ? "default" : "outline"}
                          size="sm"
                          onClick={() => {
                            console.log("Toggling sample mode:", !useSampleCode);
                            setUseSampleCode(!useSampleCode);
                            if (!useSampleCode) {
                              // When enabling sample mode, set duration for structured test (12 seconds = 360 frames)
                              setDurationInFrames(360);
                            }
                          }}
                          className="text-xs h-6"
                        >
                          {useSampleCode ? "✓ Sample" : "Load Sample"}
                        </Button>
                      </div>

                      <div className="flex-1 flex items-center justify-center w-full">
                        {/* Debug console log */}
                        {(() => {
                          console.log("=== RENDER DEBUG ===");
                          console.log("Generated TSX code:", generatedTsxCode?.slice(0, 100) + "...");
                          console.log("Preview content:", previewContent);
                          console.log("Preview settings:", previewSettings);
                          console.log("==================");
                          return null;
                        })()}
                        {generatedTsxCode || useSampleCode ? (
                          <DynamicVideoPlayer
                            tsxCode={generatedTsxCode}
                            useSampleCode={useSampleCode}
                            compositionWidth={previewSettings.width}
                            compositionHeight={previewSettings.height}
                            backgroundColor={previewSettings.backgroundColor}
                            playerRef={playerRef}
                            durationInFrames={durationInFrames}
                            onCodeFixed={(fixedCode) => {
                              console.log('🔧 Code automatically fixed, updating state...');
                              setGeneratedTsxCode(fixedCode);
                            }}
                            onError={handleVideoPlayerError}
                          />
                        ) : (
                          <StandaloneVideoPlayer
                            content={previewContent}
                            compositionWidth={previewSettings.width}
                            compositionHeight={previewSettings.height}
                            backgroundColor={previewSettings.backgroundColor}
                            playerRef={playerRef}
                            durationInFrames={durationInFrames}
                          />
                        )}
                      </div>
                    </div>
                  </div>
                </ResizablePanel>
              </ResizablePanelGroup>
            </ResizablePanel>
          </ResizablePanelGroup>
        </ResizablePanel>

        {/* Conditionally render chat panel - extends full height */}
        {!isChatMinimized && (
          <>
            <ResizableHandle withHandle />

            {/* Right Panel - Chat (full height) */}
            <ResizablePanel defaultSize={20} minSize={15} maxSize={35}>
              <div className="h-full border-l border-border">
                <ChatBox
                  mediaBinItems={mediaBinItems}
                  handleDropOnTrack={() => {}} // No-op since we don't have timeline
                  isMinimized={false}
                  onToggleMinimize={() => setIsChatMinimized(true)}
                  messages={chatMessages}
                  onMessagesChange={setChatMessages}
                  timelineState={{ tracks: [] }} // Empty timeline since we don't have timeline
                  isStandalonePreview={true}
                  onGenerateComposition={handleGenerateAiCompositionWithTracking}
                  isGeneratingComposition={isGenerating}
                  currentComposition={generatedTsxCode}
                  generationError={generationError}
                  onRetryFix={retryWithFix}
                  onClearError={clearError}
                />
              </div>
            </ResizablePanel>
          </>
        )}
      </ResizablePanelGroup>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="video/*,image/*,audio/*"
        multiple
        className="hidden"
        onChange={handleFileInputChange}
      />

      {/* Render Status as Toast */}
      {renderStatus && (
        <div className="fixed bottom-4 right-4 z-50">
          <RenderStatus renderStatus={renderStatus} />
        </div>
      )}
    </div>
  );
}
