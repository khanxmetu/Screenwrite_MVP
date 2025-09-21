/**
 * Chat Workflow File Logger
 * 
 * Logs the entire conversational synth workflow to files for debugging
 */

import { apiUrl } from "./api";

interface ChatLogEntry {
  timestamp: string;
  step: string;
  data: any;
  error?: string;
}

class ChatWorkflowLogger {
  private logEntries: ChatLogEntry[] = [];
  private sessionId: string;

  constructor() {
    this.sessionId = `chat_${Date.now()}`;
  }

  async log(step: string, data: any, error?: string) {
    const entry: ChatLogEntry = {
      timestamp: new Date().toISOString(),
      step,
      data,
      error
    };
    
    this.logEntries.push(entry);
    
    // Also log to console for immediate debugging
    const prefix = error ? '❌' : '📝';
    console.log(`${prefix} [${step}]`, data);
    if (error) console.error('Error:', error);

    // Immediately save to backend
    await this.saveEntry(entry);
  }

  async saveEntry(entry: ChatLogEntry) {
    try {
      const response = await fetch(apiUrl('/chat/log', true), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: this.sessionId,
          log_entry: entry
        })
      });

      if (!response.ok) {
        console.error('Failed to save log entry:', await response.text());
      }
    } catch (error) {
      console.error('❌ Failed to save log entry:', error);
    }
  }

  async saveToFile() {
    // No longer needed - entries are saved immediately
    console.log(`📁 Chat workflow logged to backend: chat_workflow_${this.sessionId}.json`);
  }

  // Specific logging methods for different workflow steps
  async logUserMessage(message: string, mentionedFiles: string[]) {
    await this.log('USER_MESSAGE', { message, mentionedFiles });
  }

  async logSynthCall(message: string, context: any) {
    await this.log('SYNTH_CALL', { message, context: this.sanitizeContext(context) });
  }

  async logSynthResponse(response: any) {
    await this.log('SYNTH_RESPONSE', response);
  }

  async logProbeStart(fileName: string, question: string) {
    await this.log('PROBE_START', { fileName, question });
  }

  async logProbeAnalysis(fileName: string, analysis: string) {
    await this.log('PROBE_ANALYSIS', { fileName, analysis });
  }

  async logProbeError(fileName: string, error: string) {
    await this.log('PROBE_ERROR', { fileName }, error);
  }

  async logEditExecution(instructions: string) {
    await this.log('EDIT_EXECUTION', { instructions });
  }

  async logEditResult(success: boolean, error?: string) {
    await this.log('EDIT_RESULT', { success }, error);
  }

  async logChatResponse(content: string) {
    await this.log('CHAT_RESPONSE', { content });
  }

  async logWorkflowComplete() {
    await this.log('WORKFLOW_COMPLETE', { totalSteps: this.logEntries.length });
    await this.saveToFile();
  }

  // Sanitize context to avoid logging sensitive data
  private sanitizeContext(context: any) {
    return {
      messagesCount: context.messages?.length || 0,
      hasComposition: !!context.currentComposition,
      mediaLibraryCount: context.mediaLibrary?.length || 0,
      compositionDuration: context.compositionDuration
    };
  }
}

// Export singleton instance
export const chatLogger = new ChatWorkflowLogger();

// Export helper functions for easy logging
export const logUserMessage = (message: string, mentionedFiles: string[]) => 
  chatLogger.logUserMessage(message, mentionedFiles);

export const logSynthCall = (message: string, context: any) => 
  chatLogger.logSynthCall(message, context);

export const logSynthResponse = (response: any) => 
  chatLogger.logSynthResponse(response);

export const logProbeStart = (fileName: string, question: string) => 
  chatLogger.logProbeStart(fileName, question);

export const logProbeAnalysis = (fileName: string, analysis: string) => 
  chatLogger.logProbeAnalysis(fileName, analysis);

export const logProbeError = (fileName: string, error: string) => 
  chatLogger.logProbeError(fileName, error);

export const logEditExecution = (instructions: string) => 
  chatLogger.logEditExecution(instructions);

export const logEditResult = (success: boolean, error?: string) => 
  chatLogger.logEditResult(success, error);

export const logChatResponse = (content: string) => 
  chatLogger.logChatResponse(content);

export const logWorkflowComplete = () => 
  chatLogger.logWorkflowComplete();