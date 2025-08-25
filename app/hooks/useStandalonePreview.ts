import { useState, useCallback } from "react";
import { type PreviewContent } from "~/video-compositions/StandalonePreview";
import { generateComposition, type CompositionRequest, type ConversationMessage } from "~/utils/api";

export interface PreviewSettings {
  width: number;
  height: number;
  backgroundColor: string;
  fps: number;
  synthThinkingBudget: number;
  codeGenThinkingBudget: number;
}

// Default boilerplate Remotion composition - matches AI output format
const BOILERPLATE_COMPOSITION = `const frame = useCurrentFrame();
const { fps } = useVideoConfig();

return React.createElement(AbsoluteFill, {
  style: {
    backgroundColor: '#000000',
    justifyContent: 'center',
    alignItems: 'center'
  }
});`;

// Hook to manage standalone preview content
export function useStandalonePreview(onDurationUpdate?: (durationInFrames: number) => void) {
  const [previewContent, setPreviewContent] = useState<PreviewContent[]>([]);
  const [generatedTsxCode, setGeneratedTsxCode] = useState<string>(BOILERPLATE_COMPOSITION);
  const [previewSettings, setPreviewSettings] = useState<PreviewSettings>({
    width: 1920,
    height: 1080,
    backgroundColor: "#000000",
    fps: 30,
    synthThinkingBudget: 2000,
    codeGenThinkingBudget: 3000,
  });
  const [isGenerating, setIsGenerating] = useState(false);
  const [lastAiExplanation, setLastAiExplanation] = useState<string>("");
  const [conversationHistory, setConversationHistory] = useState<ConversationMessage[]>([]);

  // Add content to preview
  const addPreviewContent = useCallback((content: PreviewContent) => {
    setPreviewContent(prev => [...prev, content]);
  }, []);

  // Remove content from preview
  const removePreviewContent = useCallback((id: string) => {
    setPreviewContent(prev => prev.filter(item => item.id !== id));
  }, []);

  // Update specific content
  const updatePreviewContent = useCallback((id: string, updates: Partial<PreviewContent>) => {
    setPreviewContent(prev =>
      prev.map(item =>
        item.id === id ? { ...item, ...updates } : item
      )
    );
  }, []);

  // Clear all content
  const clearPreviewContent = useCallback(() => {
    setPreviewContent([]);
    setGeneratedTsxCode(BOILERPLATE_COMPOSITION);
    setLastAiExplanation("");
    setConversationHistory([]); // Clear conversation history too
  }, []);

  // Generate content using AI
  const generateAiContent = useCallback(async (userRequest: string, mediaBinItems: any[] = []): Promise<boolean> => {
    setIsGenerating(true);
    console.log("🤖 Generating AI TSX code for request:", userRequest);
    console.log("📂 Available media files:", mediaBinItems.length);
    console.log("📜 Conversation history entries:", conversationHistory.length);

    try {
      const request: CompositionRequest = {
        user_request: userRequest,
        current_content: previewContent,
        preview_settings: previewSettings,
        media_library: mediaBinItems,
        current_generated_code: generatedTsxCode,
        conversation_history: conversationHistory, // Include conversation history
      };

      const response = await generateComposition(request);
      
      if (response.success && response.composition_code) {
        console.log("✅ AI TSX generation successful:", response.composition_code);
        console.log("🎬 AI-determined duration:", response.duration, "seconds");
        
        setGeneratedTsxCode(response.composition_code);
        setLastAiExplanation(response.explanation);
        setPreviewContent([]); // Clear old content since we're using TSX now

        // Update duration in the parent component
        if (onDurationUpdate && response.duration && response.duration > 0) {
          const durationInFrames = Math.round(response.duration * previewSettings.fps);
          console.log("🎯 Updating frontend duration to:", durationInFrames, "frames");
          onDurationUpdate(durationInFrames);
        }

        // Add this interaction to conversation history
        const newHistoryEntry: ConversationMessage = {
          user_request: userRequest,
          ai_response: response.explanation,
          generated_code: response.composition_code,
          timestamp: new Date().toISOString(),
        };
        setConversationHistory(prev => [...prev, newHistoryEntry]);
        console.log("📝 Added to conversation history:", newHistoryEntry);

        return true;
      } else {
        console.error("❌ AI TSX generation failed:", response.error_message);
        console.log("🔄 Keeping previous composition and duration unchanged");
        // Don't update any state - keep previous composition and duration
        return false;
      }
    } catch (error) {
      console.error("❌ Error generating AI TSX code:", error);
      return false;
    } finally {
      setIsGenerating(false);
    }
  }, [previewContent, previewSettings, generatedTsxCode, conversationHistory, onDurationUpdate]);

  // Load sample content for testing
  const loadSampleContent = useCallback(() => {
    const sampleContent: PreviewContent[] = [
      {
        id: "sample-text-1",
        type: "text",
        text: {
          content: "Welcome to Screenwrite!",
          fontSize: 64,
          color: "#ffffff",
          fontFamily: "Arial, sans-serif",
          textAlign: "center",
          fontWeight: "bold",
        },
        position: {
          x: 100,
          y: 100,
          width: 1720,
          height: 200,
        },
        duration: 3,
      },
      {
        id: "sample-text-2",
        type: "text",
        text: {
          content: "This preview is independent from the timeline",
          fontSize: 32,
          color: "#00ff00",
          fontFamily: "Arial, sans-serif",
          textAlign: "center",
          fontWeight: "normal",
        },
        position: {
          x: 200,
          y: 400,
          width: 1520,
          height: 100,
        },
        duration: 4,
      },
      {
        id: "sample-text-3",
        type: "text",
        text: {
          content: "Watch me slide in!",
          fontSize: 48,
          color: "#ff6b6b",
          fontFamily: "Arial, sans-serif",
          textAlign: "center",
          fontWeight: "bold",
        },
        position: {
          x: -500, // Start off-screen
          y: 600,
          width: 800,
          height: 150,
        },
        duration: 6,
      },
      {
        id: "sample-text-4",
        type: "text",
        text: {
          content: "🎬 Testing Animation!",
          fontSize: 72,
          color: "#ffd93d",
          fontFamily: "Arial, sans-serif",
          textAlign: "center",
          fontWeight: "bold",
        },
        position: {
          x: 500,
          y: 300,
          width: 920,
          height: 200,
        },
        duration: 8,
      },
    ];
    setPreviewContent(sampleContent);
  }, []);

  // Update preview settings
  const updatePreviewSettings = useCallback((updates: Partial<PreviewSettings>) => {
    setPreviewSettings(prev => ({ ...prev, ...updates }));
  }, []);

  return {
    previewContent,
    generatedTsxCode,
    previewSettings,
    isGenerating,
    lastAiExplanation,
    conversationHistory, // Expose conversation history
    addPreviewContent,
    removePreviewContent,
    updatePreviewContent,
    clearPreviewContent,
    generateAiContent,
    loadSampleContent,
    updatePreviewSettings,
    setPreviewContent,
    setPreviewSettings,
    setGeneratedTsxCode, // Export function to update generated TSX code
  };
}
