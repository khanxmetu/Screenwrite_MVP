import { useState, useCallback } from "react";
import { type PreviewContent } from "~/video-compositions/StandalonePreview";
import { generateComposition, fixCode, type CompositionRequest, type ConversationMessage, type CodeFixRequest } from "~/utils/api";

export interface PreviewSettings {
  width: number;
  height: number;
  backgroundColor: string;
  fps: number;
  synthThinkingBudget: number;
  codeGenThinkingBudget: number;
}

export interface GenerationError {
  hasError: boolean;
  errorMessage: string;
  errorStack?: string;
  brokenCode: string;
  originalRequest: string;
  canRetry: boolean;
}

// Helper function to provide better error messages for common syntax errors
const improveErrorMessage = (error: Error): string => {
  const message = error.message;
  
  // Common JavaScript syntax error patterns
  if (message.includes("Unexpected token")) {
    return `Syntax Error: ${message}. Check for missing commas, brackets, or quotes.`;
  }
  if (message.includes("Unexpected end of input")) {
    return "Syntax Error: Code appears to be incomplete. Missing closing brackets or parentheses.";
  }
  if (message.includes("Invalid or unexpected token")) {
    return `Syntax Error: ${message}. Check for invalid characters or malformed code.`;
  }
  
  // Return original message for other errors
  return message;
};

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
  const [generationError, setGenerationError] = useState<GenerationError>({
    hasError: false,
    errorMessage: "",
    brokenCode: "",
    originalRequest: "",
    canRetry: false,
  });

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
    setGenerationError({
      hasError: false,
      errorMessage: "",
      brokenCode: "",
      originalRequest: "",
      canRetry: false,
    });
  }, []);

  // Clear error state
  const clearError = useCallback(() => {
    setGenerationError({
      hasError: false,
      errorMessage: "",
      brokenCode: "",
      originalRequest: "",
      canRetry: false,
    });
  }, []);

  // Retry failed generation by fixing the code
  const retryWithFix = useCallback(async (): Promise<boolean> => {
    if (!generationError.hasError || !generationError.canRetry) {
      return false;
    }

    setIsGenerating(true);
    console.log("🔧 Attempting to fix broken code:", generationError.errorMessage);

    try {
      const fixRequest: CodeFixRequest = {
        broken_code: generationError.brokenCode,
        error_message: generationError.errorMessage,
        error_stack: generationError.errorStack,
        media_library: [], // Not needed for syntax fixes
      };

      const fixResponse = await fixCode(fixRequest);

      if (fixResponse.success && fixResponse.corrected_code) {
        console.log("✅ Code fix successful");
        
        // Clear error state
        setGenerationError({
          hasError: false,
          errorMessage: "",
          brokenCode: "",
          originalRequest: "",
          canRetry: false,
        });

        // Apply the fixed code
        setGeneratedTsxCode(fixResponse.corrected_code);
        setLastAiExplanation(`${fixResponse.explanation} (Auto-fixed)`);

        // Update duration if provided
        if (onDurationUpdate && fixResponse.duration && fixResponse.duration > 0) {
          const durationInFrames = Math.round(fixResponse.duration * previewSettings.fps);
          onDurationUpdate(durationInFrames);
        }

        return true;
      } else {
        console.error("❌ Code fix failed:", fixResponse.error_message);
        
        // Update error state to indicate fix attempt failed
        setGenerationError(prev => ({
          ...prev,
          errorMessage: `Fix attempt failed: ${fixResponse.error_message || 'Unknown error'}`,
          canRetry: true, // Allow another retry attempt
        }));
        
        return false;
      }
    } catch (error) {
      console.error("❌ Error during code fix:", error);
      
      // Update error state to indicate fix attempt failed
      setGenerationError(prev => ({
        ...prev,
        errorMessage: `Fix attempt failed: ${error instanceof Error ? error.message : String(error)}`,
        canRetry: true, // Allow another retry attempt
      }));
      
      return false;
    } finally {
      setIsGenerating(false);
    }
  }, [generationError, onDurationUpdate, previewSettings.fps]);

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
        
        // Test the generated code for syntax errors before setting it
        try {
          // Try to parse the generated code to check for syntax errors
          new Function(response.composition_code);
          
          // If no syntax error, proceed with setting the code
          setGeneratedTsxCode(response.composition_code);
          setLastAiExplanation(response.explanation);
          setPreviewContent([]); // Clear old content since we're using TSX now

          // Clear any previous error state
          setGenerationError({
            hasError: false,
            errorMessage: "",
            brokenCode: "",
            originalRequest: "",
            canRetry: false,
          });

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
        } catch (syntaxError) {
          // Syntax error detected - set error state for retry
          console.error("❌ Syntax error in generated code:", syntaxError);
          
          const errorMessage = syntaxError instanceof Error 
            ? improveErrorMessage(syntaxError)
            : String(syntaxError);
          
          setGenerationError({
            hasError: true,
            errorMessage,
            errorStack: syntaxError instanceof Error ? syntaxError.stack : undefined,
            brokenCode: response.composition_code,
            originalRequest: userRequest,
            canRetry: true,
          });

          return false;
        }
      } else {
        console.error("❌ AI TSX generation failed:", response.error_message);
        console.log("🔄 Keeping previous composition and duration unchanged");
        
        // Set error state for API failures
        setGenerationError({
          hasError: true,
          errorMessage: response.error_message || "Generation failed",
          brokenCode: "",
          originalRequest: userRequest,
          canRetry: false, // API failures can't be fixed, only regenerated
        });
        
        return false;
      }
    } catch (error) {
      console.error("❌ Error generating AI TSX code:", error);
      
      // Set error state for network/API errors
      setGenerationError({
        hasError: true,
        errorMessage: error instanceof Error ? error.message : String(error),
        errorStack: error instanceof Error ? error.stack : undefined,
        brokenCode: "",
        originalRequest: userRequest,
        canRetry: false, // Network errors can't be fixed, only regenerated
      });
      
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
    generationError, // Expose error state
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
    retryWithFix, // Export retry function
    clearError, // Export error clearing function
  };
}
