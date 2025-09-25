import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Bot,
  User,
  ChevronDown,
  AtSign,
  FileVideo,
  FileImage,
  Type,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  X,
} from "lucide-react";
import { Button } from "~/components/ui/button";
import { type MediaBinItem, type TimelineState } from "../timeline/types";
import { cn } from "~/lib/utils";
import axios from "axios";
import { apiUrl } from "~/utils/api";
import { 
  logUserMessage, 
  logSynthCall, 
  logSynthResponse, 
  logProbeStart, 
  logProbeAnalysis, 
  logProbeError,
  logEditExecution,
  logEditResult,
  logChatResponse,
  logWorkflowComplete 
} from "~/utils/fileLogger";

// llm tools
import { llmAddScrubberToTimeline } from "~/utils/llm-handler";

// Conversational Synth
import { ConversationalSynth, type SynthContext, type ConversationMessage, type SynthResponse } from "./ConversationalSynth";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  isExplanationMode?: boolean; // For post-edit explanations
  isAnalysisResult?: boolean; // For analysis results that appear in darker bubbles
}

interface ChatBoxProps {
  className?: string;
  mediaBinItems: MediaBinItem[];
  handleDropOnTrack: (
    item: MediaBinItem,
    trackId: string,
    dropLeftPx: number
  ) => void;
  isMinimized?: boolean;
  onToggleMinimize?: () => void;
  messages: Message[];
  onMessagesChange: (updater: (messages: Message[]) => Message[]) => void;
  timelineState: TimelineState;
  // New props for AI composition generation
  isStandalonePreview?: boolean;
  onGenerateComposition?: (userRequest: string, mediaBinItems: MediaBinItem[]) => Promise<boolean>;
  isGeneratingComposition?: boolean;
  // Props for conversational edit system
  currentComposition?: string; // Current TSX composition code
  // Error handling props
  generationError?: {
    hasError: boolean;
    errorMessage: string;
    errorStack?: string;
    brokenCode: string;
    originalRequest: string;
    canRetry: boolean;
  };
  onRetryFix?: () => Promise<boolean>;
  onClearError?: () => void;
}

export function ChatBox({
  className = "",
  mediaBinItems,
  handleDropOnTrack,
  isMinimized = false,
  onToggleMinimize,
  messages,
  onMessagesChange,
  timelineState,
  isStandalonePreview = false,
  onGenerateComposition,
  isGeneratingComposition = false,
  currentComposition,
  generationError,
  onRetryFix,
  onClearError,
}: ChatBoxProps) {
  const [inputValue, setInputValue] = useState("");
  const [showMentions, setShowMentions] = useState(false);
  const [showSendOptions, setShowSendOptions] = useState(false);
  const [mentionQuery, setMentionQuery] = useState("");
  const [selectedMentionIndex, setSelectedMentionIndex] = useState(0);
  const [cursorPosition, setCursorPosition] = useState(0);
  const [textareaHeight, setTextareaHeight] = useState(36); // Starting height for proper size
  const [sendWithMedia, setSendWithMedia] = useState(false); // Track send mode
  const [mentionedItems, setMentionedItems] = useState<MediaBinItem[]>([]); // Store actual mentioned items
  const [collapsedMessages, setCollapsedMessages] = useState<Set<string>>(new Set()); // Track collapsed analysis results
  const [isInSynthLoop, setIsInSynthLoop] = useState(false); // Track when unified workflow is active
  const [pendingProbe, setPendingProbe] = useState<{
    fileName: string, 
    question: string, 
    originalMessage: string, 
    conversationMessages: ConversationMessage[], 
    synthContext: SynthContext
  } | null>(null);

  // Initialize Conversational Synth
  const [synth] = useState(() => new ConversationalSynth("dummy-api-key")); // Will use actual API key later
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const mentionsRef = useRef<HTMLDivElement>(null);
  const sendOptionsRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // Click outside handler for send options
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        sendOptionsRef.current &&
        !sendOptionsRef.current.contains(event.target as Node)
      ) {
        setShowSendOptions(false);
      }
    };

    if (showSendOptions) {
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [showSendOptions]);

  // Monitor for video uploads completing and retry pending probes
  useEffect(() => {
    if (pendingProbe) {
      const mediaFile = mediaBinItems.find(item => item.name === pendingProbe.fileName);
      if (mediaFile?.gemini_file_id) {
        console.log("🔄 Retrying pending probe for:", pendingProbe.fileName);
        // Clear pending probe and retry
        const { fileName, question, originalMessage, conversationMessages, synthContext } = pendingProbe;
        setPendingProbe(null);
        
        // Add "now analyzing" message to show the retry is happening
        const analyzingMessage: Message = {
          id: Date.now().toString(),
          content: `Video ready! Now analyzing ${fileName}...`,
          isUser: false,
          timestamp: new Date(),
        };
        onMessagesChange(prevMessages => [...prevMessages, analyzingMessage]);
        
        // Retry the probe using the main flow with all context
        handleProbeRequest(fileName, question, originalMessage, conversationMessages, synthContext).then(newMessages => {
          onMessagesChange(prevMessages => [...prevMessages, ...newMessages]);
        }).catch(error => {
          console.error("❌ Retry failed:", error);
          const errorMessage: Message = {
            id: Date.now().toString(),
            content: `❌ Analysis retry failed: ${error.message}`,
            isUser: false,
            timestamp: new Date(),
          };
          onMessagesChange(prevMessages => [...prevMessages, errorMessage]);
        });
      }
    }
  }, [mediaBinItems, pendingProbe]);

  // Filter media bin items based on mention query
  const filteredMentions = mediaBinItems.filter((item) =>
    item.name.toLowerCase().includes(mentionQuery.toLowerCase())
  );

  // Handle input changes and @ mention detection
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    const cursorPos = e.target.selectionStart || 0;

    setInputValue(value);
    setCursorPosition(cursorPos);

    // Auto-resize textarea
    const textarea = e.target;
    textarea.style.height = "auto";
    const newHeight = Math.min(textarea.scrollHeight, 96); // max about 4 lines
    textarea.style.height = newHeight + "px";
    setTextareaHeight(newHeight);

    // Clean up mentioned items that are no longer in the text
    const mentionPattern = /@(\w+(?:\s+\w+)*)/g;
    const currentMentions = Array.from(value.matchAll(mentionPattern)).map(match => match[1]);
    setMentionedItems(prev => prev.filter(item => 
      currentMentions.some(mention => mention.toLowerCase() === item.name.toLowerCase())
    ));

    // Check for @ mentions
    const beforeCursor = value.slice(0, cursorPos);
    const lastAtIndex = beforeCursor.lastIndexOf("@");

    if (lastAtIndex !== -1) {
      const afterAt = beforeCursor.slice(lastAtIndex + 1);
      // Only show mentions if @ is at start or after whitespace, and no spaces after @
      const isValidMention =
        (lastAtIndex === 0 || /\s/.test(beforeCursor[lastAtIndex - 1])) &&
        !afterAt.includes(" ");

      if (isValidMention) {
        setMentionQuery(afterAt);
        setShowMentions(true);
        setSelectedMentionIndex(0);
      } else {
        setShowMentions(false);
      }
    } else {
      setShowMentions(false);
    }
  };

  // Insert mention into input
  const insertMention = (item: MediaBinItem) => {
    const beforeCursor = inputValue.slice(0, cursorPosition);
    const afterCursor = inputValue.slice(cursorPosition);
    const lastAtIndex = beforeCursor.lastIndexOf("@");

    const newValue =
      beforeCursor.slice(0, lastAtIndex) + `@${item.name} ` + afterCursor;
    setInputValue(newValue);
    setShowMentions(false);

    // Store the actual item reference for later use
    setMentionedItems(prev => {
      // Avoid duplicates
      if (!prev.find(existingItem => existingItem.id === item.id)) {
        return [...prev, item];
      }
      return prev;
    });

    // Focus back to input
    setTimeout(() => {
      inputRef.current?.focus();
      const newCursorPos = lastAtIndex + item.name.length + 2;
      inputRef.current?.setSelectionRange(newCursorPos, newCursorPos);
    }, 0);
  };

  // Simple internal probe handler that just does media analysis (no nested synth calls)
  const handleProbeRequestInternal = async (
    fileName: string, 
    question: string
  ): Promise<Message[]> => {
    await logProbeStart(fileName, question);
    console.log("🔍 Executing probe request for:", fileName);
    console.log("🔍 Available media files:", mediaBinItems.map(item => item.name));
    
    // Smart file matching logic
    let mediaFile = mediaBinItems.find(item => item.name === fileName);
    
    // If exact match not found, try fuzzy matching or default selection
    if (!mediaFile) {
      // If no filename provided or not found, and only one media file exists, use it
      if (mediaBinItems.length === 1) {
        mediaFile = mediaBinItems[0];
        console.log(`🔍 Using only available media file: ${mediaFile.name}`);
      } else {
        // Try partial name matching
        mediaFile = mediaBinItems.find(item => 
          item.name.toLowerCase().includes(fileName.toLowerCase()) ||
          fileName.toLowerCase().includes(item.name.toLowerCase())
        );
      }
    }
    
    if (!mediaFile) {
      const availableFiles = mediaBinItems.map(f => f.name).join(', ');
      await logProbeError(fileName, `Media file not found. Available files: ${availableFiles}`);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `❌ Could not find media file: ${fileName}. Available files: ${availableFiles}`,
        isUser: false,
        timestamp: new Date(),
      };
      return [errorMessage];
    }

    try {
      // Call Gemini Vision API to analyze the media file
      const analysisResult = await analyzeMediaWithGemini(mediaFile, question);
      await logProbeAnalysis(fileName, analysisResult);
      
      // Create analysis result message (just return the analysis, don't call synth)
      const analysisMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: analysisResult,
        isUser: false,
        timestamp: new Date(),
        isAnalysisResult: true,
      };

      // Immediately add to collapsed state so it appears collapsed from the start
      setCollapsedMessages(prev => {
        const newSet = new Set(prev);
        newSet.add(analysisMessage.id);
        return newSet;
      });

      return [analysisMessage];

    } catch (error) {
      console.error("❌ Probe analysis failed:", error);
      await logProbeError(fileName, error instanceof Error ? error.message : String(error));
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `❌ Failed to analyze ${fileName}. ${error instanceof Error ? error.message : 'Unknown error'}`,
        isUser: false,
        timestamp: new Date(),
        isAnalysisResult: true,
      };
      return [errorMessage];
    }
  };

  const handleProbeRequest = async (
    fileName: string, 
    question: string, 
    originalMessage: string, 
    conversationMessages: ConversationMessage[],
    synthContext: SynthContext
  ): Promise<Message[]> => {
    // Check if this is a video without gemini_file_id (race condition)
    const mediaFile = mediaBinItems.find(item => item.name === fileName);
    const fileExtension = mediaFile?.name.split('.').pop()?.toLowerCase();
    const isVideo = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'].includes(fileExtension || '');
    
    if (mediaFile && isVideo && !mediaFile.gemini_file_id) {
      console.log("⏳ Video still uploading, storing pending probe:", fileName);
      setPendingProbe({ fileName, question, originalMessage, conversationMessages, synthContext });
      
      // Return a pending message
      const pendingMessage: Message = {
        id: Date.now().toString(),
        content: `Video is still being uploaded for analysis. Your request will continue automatically once ready...`,
        isUser: false,
        timestamp: new Date(),
      };
      return [pendingMessage];
    }

    // Otherwise, proceed with simple probe execution (unified system handles continuation)
    return handleProbeRequestInternal(fileName, question);
  };

  const analyzeMediaWithGemini = async (mediaFile: MediaBinItem, question: string): Promise<string> => {
    const GEMINI_API_KEY = import.meta.env.VITE_GEMINI_API_KEY;
    const GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent";

    if (!GEMINI_API_KEY) {
      throw new Error("GEMINI_API_KEY not found. Please set VITE_GEMINI_API_KEY in your environment.");
    }

    const fileExtension = mediaFile.name.split('.').pop()?.toLowerCase();
    const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(fileExtension || '');
    const isVideo = ['mp4', 'mov', 'avi', 'webm'].includes(fileExtension || '');
    
    if (!isImage && !isVideo) {
      throw new Error(`Unsupported file type: ${fileExtension}. Only images and videos can be analyzed.`);
    }

    try {
      let requestBody: any;

      if (isVideo && mediaFile.gemini_file_id) {
        // For videos, use the backend video analysis endpoint
        console.log("🔍 Using backend video analysis for:", mediaFile.gemini_file_id);
        
        const response = await fetch(apiUrl('/analyze-video', true), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            gemini_file_id: mediaFile.gemini_file_id,
            question: question
          })
        });

        if (!response.ok) {
          throw new Error(`Backend video analysis failed: ${response.status}`);
        }

        const result = await response.json();
        
        if (!result.success) {
          throw new Error(result.error_message || 'Video analysis failed');
        }

        return result.analysis;
      } else if (isVideo && !mediaFile.gemini_file_id) {
        // Video without Gemini file ID - should not happen as videos are uploaded on add
        throw new Error("Video file is still being processed for analysis. Please wait a moment and try again.");
      } else {
        // For images, use base64 inline data
        const fileUrl = mediaFile.mediaUrlRemote || mediaFile.mediaUrlLocal;
        console.log("🔍 Media file URLs:", { remote: mediaFile.mediaUrlRemote, local: mediaFile.mediaUrlLocal, using: fileUrl });
        
        if (!fileUrl) {
          throw new Error("No valid media URL found for this file");
        }
        
        const response = await fetch(fileUrl);
        if (!response.ok) {
          throw new Error(`Failed to fetch media file: ${response.status} ${response.statusText}`);
        }
        const blob = await response.blob();
        console.log("🔍 Blob info:", { type: blob.type, size: blob.size });
        
        const base64Data = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => {
            const result = reader.result as string;
            // Remove the data:mime/type;base64, prefix
            const base64 = result.split(',')[1];
            resolve(base64);
          };
          reader.onerror = reject;
          reader.readAsDataURL(blob);
        });

        requestBody = {
          contents: [
            {
              parts: [
                {
                  text: question
                },
                {
                  inline_data: {
                    mime_type: blob.type,
                    data: base64Data
                  }
                }
              ]
            }
          ],
          generationConfig: {
            temperature: 0.1
          }
        };
      }

      const apiResponse = await fetch(`${GEMINI_API_URL}?key=${GEMINI_API_KEY}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (!apiResponse.ok) {
        const errorData = await apiResponse.json().catch(() => ({}));
        throw new Error(`Gemini API error: ${apiResponse.status} - ${errorData.error?.message || 'Unknown error'}`);
      }

      const data = await apiResponse.json();
      console.log("🔍 Gemini Vision API response:", JSON.stringify(data, null, 2));
      
      if (!data.candidates || !data.candidates[0] || !data.candidates[0].content) {
        console.error("❌ Missing candidates or content in response:", data);
        throw new Error('Invalid response format from Gemini API - no candidates or content');
      }

      const candidate = data.candidates[0];
      const content = candidate.content;
      
      if (!content.parts || !Array.isArray(content.parts) || content.parts.length === 0) {
        console.error("❌ Missing parts in content:", content);
        throw new Error('Invalid response format from Gemini API - no parts in content');
      }
      
      const firstPart = content.parts[0];
      if (!firstPart || !firstPart.text) {
        console.error("❌ Missing text in first part:", firstPart);
        throw new Error('Invalid response format from Gemini API - no text in first part');
      }

      return firstPart.text;

    } catch (error) {
      console.error("❌ Gemini Vision API failed:", error);
      throw error;
    }
  };

  // Simple internal handlers that just execute actions (no nested synth calls)
  const handleGenerateRequestInternal = async (
    prompt: string,
    suggestedName: string,
    description: string
  ): Promise<Message[]> => {
    console.log("🎨 Executing generation request:", { prompt, suggestedName, description });
    
    try {
      // For now, mock the image generation (will implement actual backend call later)
      console.log("🎨 Mocking image generation for:", prompt);
      
      // Simulate generation delay
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock generated filename (will be returned from backend later)
      const generatedFileName = `${suggestedName}.png`;
      
      // Create generation result message
      const generationMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `✨ Generated: ${generatedFileName}`,
        isUser: false,
        timestamp: new Date(),
      };

      // Note: In real implementation, this would call backend to generate and add to media library
      // For now, just return the completion message
      return [generationMessage];

    } catch (error) {
      console.error("❌ Generation failed:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `❌ Failed to generate image: ${error instanceof Error ? error.message : 'Unknown error'}`,
        isUser: false,
        timestamp: new Date(),
      };
      return [errorMessage];
    }
  };

  const handleConversationalMessage = async (messageContent: string): Promise<void> => {
    await logUserMessage(messageContent, mentionedItems.map(item => item.name));
    console.log("🧠 Processing conversational message with unified workflow:", messageContent);

    // Initialize unified workflow state
    let currentMessageContent = messageContent;
    let allResponseMessages: Message[] = [];
    let continueWorkflow = true;
    let iterationCount = 0;
    const MAX_ITERATIONS = 10; // Prevent infinite loops
    
    // Start the loading indicator for the entire workflow
    setIsInSynthLoop(true);
    
    try {
      // Unified workflow loop: synth → route → execute → check continuation → repeat until sleep
      while (continueWorkflow && iterationCount < MAX_ITERATIONS) {
        iterationCount++;
        console.log(`🔄 Unified workflow iteration ${iterationCount}`);
      
      try {
        // Build current conversation state (including all new messages from this workflow)
        const conversationMessages: ConversationMessage[] = [
          ...messages.map(msg => ({
            id: msg.id,
            content: msg.content,
            isUser: msg.isUser,
            timestamp: msg.timestamp
          })),
          ...allResponseMessages.map(msg => ({
            id: msg.id,
            content: msg.content,
            isUser: msg.isUser,
            timestamp: msg.timestamp
          }))
        ];

        // Build synth context with latest state
        const synthContext: SynthContext = {
          messages: conversationMessages,
          currentComposition: currentComposition ? JSON.parse(currentComposition) : undefined,
          mediaLibrary: mediaBinItems,
          compositionDuration: undefined
        };

        // Call synth for decision
        await logSynthCall(currentMessageContent, synthContext);
        
        const synthResponse = await synth.processMessage(currentMessageContent, synthContext);
        await logSynthResponse(synthResponse);
        
        console.log(`🎯 Synth response type: ${synthResponse.type}`);

        // Route to appropriate handler and execute action
        const stepMessages = await executeResponseAction(synthResponse, currentMessageContent, conversationMessages, synthContext);
        
        // Add step messages to our collection
        allResponseMessages.push(...stepMessages);
        
        // Update UI immediately with new messages
        onMessagesChange(prevMessages => [...prevMessages, ...stepMessages]);

        // Check if workflow should continue
        if (synthResponse.type === 'sleep') {
          console.log("💤 Sleep response - stopping unified workflow");
          continueWorkflow = false;
        } else if (synthResponse.type === 'chat') {
          console.log("💬 Chat response - continuing workflow automatically");
          // For chat responses, use the chat content as the next input to continue the workflow
          currentMessageContent = `Continue with: ${synthResponse.content}`;
        } else {
          console.log(`� ${synthResponse.type} response - continuing workflow`);
          // For other response types (edit, probe, generate), continue with original message context
          currentMessageContent = messageContent;
        }
        
      } catch (error) {
        console.error(`❌ Unified workflow iteration ${iterationCount} failed:`, error);
        await logSynthResponse({ error: error instanceof Error ? error.message : String(error) });
        
        const errorMessage: Message = {
          id: (Date.now() + iterationCount).toString(),
          content: "I'm having trouble processing your request. Let me try a different approach.",
          isUser: false,
          timestamp: new Date(),
        };
        
        // Add to both collections for consistency (UI handled here, no double addition)
        allResponseMessages.push(errorMessage);
        onMessagesChange(prevMessages => [...prevMessages, errorMessage]);
        continueWorkflow = false;
      }
    }

    if (iterationCount >= MAX_ITERATIONS) {
      console.warn("⚠️ Unified workflow hit max iterations limit");
      const maxIterationMessage: Message = {
        id: Date.now().toString(),
        content: "I've completed several steps but need to pause here. How can I help you next?",
        isUser: false,
        timestamp: new Date(),
      };
      allResponseMessages.push(maxIterationMessage);
      onMessagesChange(prevMessages => [...prevMessages, maxIterationMessage]);
    }

    // Auto-collapse any analysis result messages (removed - now handled immediately when creating messages)
    
    // Save log after complete workflow
    await logWorkflowComplete();
    
    } catch (error) {
      console.error("❌ Unified workflow failed:", error);
      // Add error message to UI
      const errorMessage: Message = {
        id: Date.now().toString(),
        content: "I'm having trouble processing your request. Please try again.",
        isUser: false,
        timestamp: new Date(),
      };
      onMessagesChange(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      // Always clear the loading indicator when workflow ends
      setIsInSynthLoop(false);
    }
    
    // Unified workflow handles all UI updates internally
    return;
  };

  // Execute the appropriate action based on response type (no nested synth calls)
  const executeResponseAction = async (
    synthResponse: SynthResponse,
    originalMessage: string,
    conversationMessages: ConversationMessage[],
    synthContext: SynthContext
  ): Promise<Message[]> => {
    console.log(`🎬 Executing action for response type: ${synthResponse.type}`);
    
    if (synthResponse.type === 'probe') {
      // Probe request - analyze media file (only show analysis result)
      console.log("🔍 Executing probe:", synthResponse.fileName, synthResponse.question);
      
      const probeResults = await handleProbeRequestInternal(synthResponse.fileName!, synthResponse.question!);
      
      return probeResults; // Only return analysis result, no "Analyzing..." message
      
    } else if (synthResponse.type === 'generate') {
      // Generate request - create image (only show generation result)
      console.log("🎨 Executing generation:", synthResponse.prompt, synthResponse.suggestedName);
      
      const generateResults = await handleGenerateRequestInternal(synthResponse.prompt!, synthResponse.suggestedName!, synthResponse.content);
      
      return generateResults; // Only return generation result, no "Generating..." message
      
    } else if (synthResponse.type === 'edit') {
      // Edit instructions - send to backend (only show final result)
      console.log("🎬 Executing edit:", synthResponse.content);
      await logEditExecution(synthResponse.content);
      
      if (onGenerateComposition) {
        const success = await onGenerateComposition(synthResponse.content, mediaBinItems);
        await logEditResult(success);
        
        const resultMessage = {
          id: (Date.now() + 1).toString(),
          content: success ? "✨ Edit implemented successfully!" : "❌ Failed to implement the edit. Please try again.",
          isUser: false,
          timestamp: new Date(),
        };
        
        return [resultMessage]; // Only return final result, no "Applying..." message
      } else {
        return [{
          id: (Date.now() + 1).toString(),
          content: "Edit instructions ready, but no implementation handler available.",
          isUser: false,
          timestamp: new Date(),
        }];
      }
      
    } else if (synthResponse.type === 'chat') {
      // Chat response - just display
      console.log("💬 Executing chat response");
      await logChatResponse(synthResponse.content);
      
      return [{
        id: (Date.now() + 1).toString(),
        content: synthResponse.content,
        isUser: false,
        timestamp: new Date(),
      }];
      
    } else if (synthResponse.type === 'sleep') {
      // Sleep response - display and mark end of workflow
      console.log("💤 Executing sleep response");
      await logChatResponse(synthResponse.content);
      
      return [{
        id: (Date.now() + 1).toString(),
        content: synthResponse.content,
        isUser: false,
        timestamp: new Date(),
      }];
      
    } else {
      // Fallback for unknown types
      console.log("❓ Executing fallback for unknown type:", synthResponse.type);
      
      return [{
        id: (Date.now() + 1).toString(),
        content: synthResponse.content,
        isUser: false,
        timestamp: new Date(),
      }];
    }
  };

  const handleSendMessage = async (includeAllMedia = false) => {
    if (!inputValue.trim()) return;

    let messageContent = inputValue.trim();
    let itemsToSend = mentionedItems;

    // If sending with all media, include all media items
    if (includeAllMedia && mediaBinItems.length > 0) {
      const mediaList = mediaBinItems.map((item) => `@${item.name}`).join(" ");
      messageContent = `${messageContent} ${mediaList}`;
      // Add all media items to the items to send
      itemsToSend = [...mentionedItems, ...mediaBinItems.filter(item => 
        !mentionedItems.find(mentioned => mentioned.id === item.id)
      )];
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      content: messageContent,
      isUser: true,
      timestamp: new Date(),
    };

    onMessagesChange(prevMessages => [...prevMessages, userMessage]);
    setInputValue("");
    setMentionedItems([]); // Clear mentioned items after sending

    // Reset textarea height
    if (inputRef.current) {
      inputRef.current.style.height = "36px"; // Back to normal height
      setTextareaHeight(36);
    }

    try {
      // Check if we're in standalone preview mode - use conversational synth
      if (isStandalonePreview) {
        console.log("🎬 Standalone preview mode - using conversational synth");
        
        // Unified workflow handles all UI updates internally, no need to add messages again
        await handleConversationalMessage(messageContent);
        
        return;
      }

      console.log("📹 Using timeline-based AI (not standalone mode)");
      // Original timeline-based AI functionality
      // Use the stored mentioned items to get their IDs
      const mentionedScrubberIds = itemsToSend.map(item => item.id);

      // Make API call to the backend
      const response = await axios.post(apiUrl("/ai", true), {
        message: messageContent,
        mentioned_scrubber_ids: mentionedScrubberIds,
        timeline_state: timelineState,
        mediabin_items: mediaBinItems,
      });

      const functionCallResponse = response.data;
      let aiResponseContent = "";

      // Handle the function call based on function_name
      if (functionCallResponse.function_call) {
        const { function_call } = functionCallResponse;
        
        try {
          if (function_call.function_name === "LLMAddScrubberToTimeline") {
            // Find the media item by ID
            const mediaItem = mediaBinItems.find(
              item => item.id === function_call.scrubber_id
            );

            if (!mediaItem) {
              aiResponseContent = `❌ Error: Media item with ID "${function_call.scrubber_id}" not found in the media bin.`;
            } else {
              // Execute the function
              llmAddScrubberToTimeline(
                function_call.scrubber_id,
                mediaBinItems,
                function_call.track_id,
                function_call.drop_left_px,
                handleDropOnTrack
              );

              aiResponseContent = `✅ Successfully added "${mediaItem.name}" to ${function_call.track_id} at position ${function_call.drop_left_px}px.`;
            }
          } else {
            aiResponseContent = `❌ Unknown function: ${function_call.function_name}`;
          }
        } catch (error) {
          aiResponseContent = `❌ Error executing function: ${
            error instanceof Error ? error.message : "Unknown error"
          }`;
        }
      } else {
        aiResponseContent = "I understand your request, but I couldn't determine a specific action to take. Could you please be more specific?";
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: aiResponseContent,
        isUser: false,
        timestamp: new Date(),
      };

      onMessagesChange(prevMessages => [...prevMessages, userMessage, aiMessage]);
    } catch (error) {
      console.error("Error calling AI API:", error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `❌ Sorry, I encountered an error while processing your request. Please try again.`,
        isUser: false,
        timestamp: new Date(),
      };
      
      onMessagesChange(prevMessages => [...prevMessages, userMessage, errorMessage]);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (showMentions && filteredMentions.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedMentionIndex((prev) =>
          prev < filteredMentions.length - 1 ? prev + 1 : 0
        );
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedMentionIndex((prev) =>
          prev > 0 ? prev - 1 : filteredMentions.length - 1
        );
        return;
      }
      if (e.key === "Enter") {
        e.preventDefault();
        insertMention(filteredMentions[selectedMentionIndex]);
        return;
      }
      if (e.key === "Escape") {
        e.preventDefault();
        setShowMentions(false);
        return;
      }
    }

    if (e.key === "Enter") {
      if (e.shiftKey) {
        // Allow default behavior for Shift+Enter (new line)
        return;
      } else {
        // Send message on Enter
        e.preventDefault();
        handleSendMessage(sendWithMedia);
      }
    }
  };

  const toggleMessageCollapsed = (messageId: string) => {
    setCollapsedMessages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  const formatMessageText = (text: string) => {
    // Simple markdown-like formatting
    return text
      .split(/(\*\*\*[^*]+\*\*\*|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|^---+$|^#{1,6}\s+.+$)/gm)
      .map((part, index) => {
        if (part.startsWith('***') && part.endsWith('***')) {
          // Bold italic
          return <strong key={index} className="font-bold italic">{part.slice(3, -3)}</strong>;
        } else if (part.startsWith('**') && part.endsWith('**')) {
          // Bold
          return <strong key={index} className="font-bold">{part.slice(2, -2)}</strong>;
        } else if (part.startsWith('*') && part.endsWith('*')) {
          // Italic
          return <em key={index} className="italic">{part.slice(1, -1)}</em>;
        } else if (part.startsWith('`') && part.endsWith('`')) {
          // Code
          return <code key={index} className="bg-gray-200 dark:bg-gray-700 px-1 py-0.5 rounded text-xs font-mono">{part.slice(1, -1)}</code>;
        } else if (/^---+$/.test(part.trim())) {
          // Horizontal rule
          return <hr key={index} className="my-2 border-gray-300 dark:border-gray-600" />;
        } else if (/^#{1,6}\s+/.test(part)) {
          // Headings
          const level = part.match(/^(#{1,6})/)?.[1].length || 1;
          const content = part.replace(/^#{1,6}\s+/, '');
          if (level === 1) {
            return <h1 key={index} className="text-lg font-bold mt-2 mb-1">{content}</h1>;
          } else if (level === 2) {
            return <h2 key={index} className="text-base font-bold mt-2 mb-1">{content}</h2>;
          } else if (level === 3) {
            return <h3 key={index} className="text-sm font-semibold mt-1 mb-1">{content}</h3>;
          } else {
            return <h4 key={index} className="text-sm font-medium mt-1 mb-1">{content}</h4>;
          }
        } else {
          // Regular text
          return part;
        }
      });
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className={`h-full flex flex-col bg-background ${className}`}>
      {/* Chat Header */}
      <div className="h-9 border-b border-border/50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 flex items-center justify-between px-3 shrink-0">
        <div className="flex items-center gap-2">
          <Bot className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-sm font-medium tracking-tight">Ask Screenwrite</span>
        </div>

        {onToggleMinimize && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleMinimize}
            className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground"
            title={isMinimized ? "Expand chat" : "Minimize chat"}
          >
            {isMinimized ? (
              <ChevronLeft className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </Button>
        )}
      </div>

      {/* Content Area */}
      <div className="flex-1 flex flex-col">
        {messages.length === 0 ? (
          // Default clean state - Copilot style
          <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
            <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
              <Bot className="h-6 w-6 text-primary" />
            </div>
            <h2 className="text-lg font-semibold mb-2">Ask Screenwrite</h2>
            <p className="text-sm text-muted-foreground mb-8 max-w-xs leading-relaxed">
              Screenwrite is your AI assistant for video editing. Ask questions, get
              help with timeline operations, or request specific edits.
            </p>
            <div className="space-y-2 text-xs text-muted-foreground">
              <div className="flex items-center gap-2">
                <AtSign className="h-3 w-3" />
                <span>to chat with media</span>
              </div>
              <div className="flex items-center gap-2">
                <kbd className="px-1.5 py-0.5 text-xs bg-muted rounded">
                  Enter
                </kbd>
                <span>to send</span>
              </div>
              <div className="flex items-center gap-2">
                <kbd className="px-1.5 py-0.5 text-xs bg-muted rounded">
                  Shift
                </kbd>
                <span>+</span>
                <kbd className="px-1.5 py-0.5 text-xs bg-muted rounded">
                  Enter
                </kbd>
                <span>for new line</span>
              </div>
            </div>
          </div>
        ) : (
          // Messages Area
          <div
            ref={scrollContainerRef}
            className="flex-1 overflow-y-auto p-3 scroll-smooth"
            style={{ maxHeight: "calc(100vh - 200px)" }}
          >
            <div className="space-y-3">
              {/* Error Display */}
              {generationError?.hasError && (
                <div className="flex justify-start">
                  <div className="max-w-[90%] rounded-lg px-3 py-3 text-xs bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 mr-8">
                    <div className="flex items-start gap-2">
                      <AlertCircle className="h-4 w-4 mt-0.5 shrink-0 text-red-600 dark:text-red-400" />
                      <div className="flex-1">
                        <div className="font-medium text-red-800 dark:text-red-200 mb-1">
                          Generation Error
                        </div>
                        <div className="text-red-700 dark:text-red-300 mb-2">
                          {generationError.errorMessage}
                        </div>
                        
                        {generationError.canRetry && onRetryFix && (
                          <div className="flex gap-2 mt-2">
                            <button
                              onClick={async () => {
                                const success = await onRetryFix();
                                if (!success) {
                                  console.error("Retry failed");
                                }
                              }}
                              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded-md transition-colors"
                              disabled={isGeneratingComposition}
                            >
                              {isGeneratingComposition ? "Fixing..." : "Try Again"}
                            </button>
                            {onClearError && (
                              <button
                                onClick={onClearError}
                                className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white text-xs rounded-md transition-colors"
                              >
                                Dismiss
                              </button>
                            )}
                          </div>
                        )}
                        
                        {!generationError.canRetry && onClearError && (
                          <button
                            onClick={onClearError}
                            className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white text-xs rounded-md transition-colors mt-2"
                          >
                            Dismiss
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${
                      message.isUser ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg px-3 py-2 text-xs ${
                        message.isUser
                          ? "bg-primary text-primary-foreground ml-8"
                          : message.isExplanationMode
                          ? "bg-green-100 dark:bg-green-900/30 border border-green-300 dark:border-green-700 mr-8"
                          : message.isAnalysisResult
                          ? "bg-slate-800 dark:bg-slate-900 text-white mr-8 cursor-pointer hover:bg-slate-700 dark:hover:bg-slate-800 transition-colors"
                          : "bg-muted mr-8"
                      }`}
                      onClick={message.isAnalysisResult ? () => toggleMessageCollapsed(message.id) : undefined}
                    >
                    <div className="flex items-start gap-2">
                      {!message.isUser && (
                        <Bot className={`h-3 w-3 mt-0.5 shrink-0 ${
                          message.isExplanationMode
                            ? "text-green-600 dark:text-green-400"
                            : message.isAnalysisResult
                            ? "text-slate-300"
                            : "text-muted-foreground"
                        }`} />
                      )}
                      <div className="flex-1 min-w-0">
                        {message.isExplanationMode && (
                          <div className="text-xs font-medium text-green-700 dark:text-green-300 mb-1">
                            📝 Changes made:
                          </div>
                        )}
                        {message.isAnalysisResult ? (
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium text-slate-200">Analysis Result</span>
                              <ChevronDown className={`h-3 w-3 transition-transform ${
                                collapsedMessages.has(message.id) ? 'rotate-180' : ''
                              }`} />
                            </div>
                            {!collapsedMessages.has(message.id) && (
                              <p className="leading-relaxed break-words overflow-wrap-anywhere">
                                {formatMessageText(message.content)}
                              </p>
                            )}
                          </div>
                        ) : (
                          <p className={`leading-relaxed break-words overflow-wrap-anywhere ${
                            message.isExplanationMode
                              ? "text-green-800 dark:text-green-200"
                              : ""
                          }`}>
                            {formatMessageText(message.content)}
                          </p>
                        )}
                        <span className="text-xs opacity-70 mt-1 block">
                          {formatTime(message.timestamp)}
                        </span>
                      </div>
                      {message.isUser && (
                        <User className="h-3 w-3 mt-0.5 text-primary-foreground/70 shrink-0" />
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {/* Simple loading indicator while in synth loop */}
              {isInSynthLoop && (
                <div className="px-3 py-2 flex items-center gap-2">
                  <div className="flex items-start gap-2">
                    <Bot className="h-3 w-3 mt-0.5 shrink-0 text-muted-foreground" />
                    <div className="flex items-center gap-1 pt-1">
                      <div className="flex space-x-1">
                        <div className="w-1 h-1 bg-muted-foreground rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                        <div className="w-1 h-1 bg-muted-foreground rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                        <div className="w-1 h-1 bg-muted-foreground rounded-full animate-bounce"></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Invisible element to scroll to */}
              <div ref={messagesEndRef} />
            </div>

            {/* Loading indicator removed - clean UI */}

            {/* Mentions popup */}
            {showMentions && (
              <div
                ref={mentionsRef}
                className="absolute bottom-full left-4 right-4 mb-2 bg-background border border-border/50 rounded-lg shadow-lg max-h-40 overflow-y-auto z-50"
              >
                {filteredMentions.map((item, index) => (
                  <div
                    key={item.id}
                    className={`px-3 py-2 text-xs cursor-pointer flex items-center gap-2 ${
                      index === selectedMentionIndex
                        ? "bg-accent text-accent-foreground"
                        : "hover:bg-muted"
                    }`}
                    onClick={() => insertMention(item)}
                  >
                    <div className="w-6 h-6 bg-muted/50 rounded flex items-center justify-center">
                      {item.mediaType === "video" ? (
                        <FileVideo className="h-3 w-3 text-muted-foreground" />
                      ) : item.mediaType === "image" ? (
                        <FileImage className="h-3 w-3 text-muted-foreground" />
                      ) : (
                        <Type className="h-3 w-3 text-muted-foreground" />
                      )}
                    </div>
                    <span className="flex-1 truncate">{item.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {item.mediaType}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Send Options Dropdown */}
            {showSendOptions && (
              <div
                ref={sendOptionsRef}
                className="absolute bottom-full right-4 mb-2 bg-background border border-border/50 rounded-md shadow-lg z-50 min-w-48"
              >
                <div className="p-1">
                  <div
                    className="px-3 py-2 text-xs cursor-pointer hover:bg-muted rounded flex items-center justify-between"
                    onClick={() => {
                      setSendWithMedia(false);
                      setShowSendOptions(false);
                      handleSendMessage(false);
                    }}
                  >
                    <span>Send</span>
                    <span className="text-xs text-muted-foreground font-mono">
                      Enter
                    </span>
                  </div>
                  <div
                    className="px-3 py-2 text-xs cursor-pointer hover:bg-muted rounded flex items-center justify-between"
                    onClick={() => {
                      setSendWithMedia(true);
                      setShowSendOptions(false);
                      handleSendMessage(true);
                    }}
                  >
                    <span>Send with all Media</span>
                  </div>
                  <div
                    className="px-3 py-2 text-xs cursor-pointer hover:bg-muted rounded flex items-center justify-between"
                    onClick={() => {
                      // Clear current messages and send to new chat
                      onMessagesChange(() => []);
                      setShowSendOptions(false);
                      handleSendMessage(false);
                    }}
                  >
                    <span>Send to New Chat</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Input Area */}
        <div className="border-t border-border/50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="p-3 relative">
            <div className="relative">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage(sendWithMedia);
                  }
                }}
                placeholder="Ask Screenwrite to create or edit your video..."
                className="w-full resize-none border-0 bg-transparent text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-0 pr-12 overflow-hidden"
                style={{ height: `${textareaHeight}px` }}
              />
              
              <div className="absolute right-2 bottom-1 flex items-center gap-1">
                {(inputValue.trim() || mentionedItems.length > 0) && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground relative"
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowSendOptions(!showSendOptions);
                    }}
                  >
                    <ChevronDown className="h-3 w-3" />
                  </Button>
                )}
                
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0 text-primary hover:text-primary/80 hover:bg-primary/10"
                  onClick={() => handleSendMessage(sendWithMedia)}
                  disabled={!inputValue.trim() && mentionedItems.length === 0}
                >
                  <Send className="h-3 w-3" />
                </Button>
              </div>
            </div>

            {mentionedItems.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2 pt-2 border-t border-border/50">
                {mentionedItems.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center gap-1 px-2 py-1 bg-muted rounded text-xs"
                  >
                    <div className="w-3 h-3 bg-muted-foreground/20 rounded flex items-center justify-center">
                      {item.mediaType === "video" ? (
                        <FileVideo className="h-2 w-2 text-muted-foreground" />
                      ) : item.mediaType === "image" ? (
                        <FileImage className="h-2 w-2 text-muted-foreground" />
                      ) : (
                        <Type className="h-2 w-2 text-muted-foreground" />
                      )}
                    </div>
                    <span className="truncate max-w-24">{item.name}</span>
                    <button
                      onClick={() => setMentionedItems(prev => prev.filter(i => i.id !== item.id))}
                      className="text-muted-foreground hover:text-foreground ml-1"
                    >
                      <X className="h-2 w-2" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}