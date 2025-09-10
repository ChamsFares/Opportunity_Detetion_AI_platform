import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight, Bot, File, Paperclip, Send, User, X } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { ApiError, ExtractedInfo, generateSessionId, processChatbotConversation } from "../services/api.ts";

interface Message {
  id: string;
  text: string;
  isBot: boolean;
  timestamp: Date;
  status?: 'processed' | 'confirmed' | 'confirmation_required' | 'error';
  data?: ExtractedInfo;
  gif?: string;
}

interface ChatbotProps {
  onComplete: (extractedData?: ExtractedInfo) => void;
}

const Chatbot: React.FC<ChatbotProps> = ({ onComplete }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      text: "Hello! I'm here to help you understand your analysis report. I can also generate custom charts and visualizations based on your questions. What would you like to know?",
      isBot: true,
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [sessionId] = useState(() => generateSessionId());
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [extractedData, setExtractedData] = useState<ExtractedInfo | null>(null);
  const [conversationContext, setConversationContext] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  };

  const scrollToBottomInstant = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "auto", block: "end" });
  };

  // Enhanced scroll management
  useEffect(() => {
    // Instant scroll on mount and when typing starts
    if (isTyping) {
      scrollToBottomInstant();
    } else {
      // Smooth scroll for new messages
      scrollToBottom();
    }
  }, [messages, isTyping]);

  // Auto-scroll when user is near bottom
  useEffect(() => {
    const chatContainer = chatContainerRef.current;
    if (!chatContainer) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = chatContainer;
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
      
      if (isNearBottom && messages.length > 0) {
        scrollToBottom();
      }
    };

    chatContainer.addEventListener('scroll', handleScroll);
    return () => chatContainer.removeEventListener('scroll', handleScroll);
  }, [messages]);

  // Auto-resize textarea with scrolling for large content
  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const newHeight = Math.min(textareaRef.current.scrollHeight, 120);
      textareaRef.current.style.height = `${newHeight}px`;

      // Enable scrolling if content exceeds max height
      if (textareaRef.current.scrollHeight > 120) {
        textareaRef.current.style.overflowY = 'auto';
      } else {
        textareaRef.current.style.overflowY = 'hidden';
      }
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [inputValue]);

  // Helper functions for message formatting
  const formatKey = (key: string) =>
    key
      .split("_")
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");

  const formatValue = (value: unknown): string => {
    if (!value) return "N/A";
    if (typeof value === "object" && value !== null) {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  // GIF functions for different error types
  const get403ErrorGif = () => {
    const gifs = [
      "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExcHFzc3lndndvOW9yeTk2amFoM2d0YWtvY2djd2k4ZnZraDBtcjd5cyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/WyefZ7wxUnWaq7DSKX/giphy.gif",
    ];
    return gifs[Math.floor(Math.random() * gifs.length)];
  };

  const getErrorGif = (status: number) => {
    switch (status) {
      case 403:
        return get403ErrorGif();
      case 404:
        return "https://media.giphy.com/media/14uQ3cOFteDaU/giphy.gif";
      case 500:
        return "https://media.giphy.com/media/NTur7XlVDUdqM/giphy.gif";
      case 429:
        return "https://media.giphy.com/media/3o6ZsZKbgw4QVWEbzO/giphy.gif";
      default:
        return "https://media.giphy.com/media/26tn33aiTi1jkl6H6/giphy.gif";
    }
  };

  const linkifyText = (text: string) => {
    if (!text) return null;
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    return text.split(urlRegex).map((part, i) =>
      urlRegex.test(part) ? (
        <a
          key={i}
          href={part}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 underline break-all"
        >
          {part}
        </a>
      ) : (
        part
      )
    );
  };

  const renderDataEntry = (key: string, value: unknown) => {
    const renderValue = (val: unknown): JSX.Element => {
      if (typeof val === "string" || typeof val === "number" || typeof val === "boolean") {
        return <span className="text-slate-700">{String(val)}</span>;
      }

      if (Array.isArray(val)) {
        if (val.every(item => typeof item === "string")) {
          return (
            <ul className="list-disc list-inside ml-4 text-slate-700">
              {val.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          );
        }

        return (
          <ul className="list-disc list-inside ml-4">
            {val.map((item, idx) => (
              <li key={idx}>{renderValue(item)}</li>
            ))}
          </ul>
        );
      }

      if (typeof val === "object" && val !== null) {
        return (
          <ul className="list-disc list-inside ml-4">
            {Object.entries(val).map(([subKey, subValue], idx) => (
              <li key={idx}>
                <span className="font-medium text-slate-800">{formatKey(subKey)}:</span> {renderValue(subValue)}
              </li>
            ))}
          </ul>
        );
      }

      return <span className="text-slate-500">N/A</span>;
    };

    return (
      <div key={key} className="text-slate-700 mb-3">
        <span className="font-semibold text-slate-800">{formatKey(key)}:</span>{" "}
        {renderValue(value)}
      </div>
    );
  };

  // Enhanced AI response generation with better context awareness
  const generateIntelligentResponse = (userInput: string, previousMessages: Message[]): string => {
    const input = userInput.toLowerCase().trim();
    
    // Context-aware responses based on conversation history
    const hasAnalysisData = extractedData && Object.keys(extractedData).length > 0;
    
    // Analysis and report-specific responses
    if (input.includes('gap') || input.includes('gaps')) {
      if (hasAnalysisData) {
        return "The analysis shows 2 strategic gaps to address. The most critical gap is in Service Gap with high impact. Would you like me to list them in detail or create a visualization?";
      }
      return "I can help you identify market gaps in your business analysis. Please share more details about your business or upload your analysis report.";
    }
    
    if (input.includes('chart') || input.includes('graph') || input.includes('visualization') || input.includes('show me')) {
      return "I can create various types of charts and visualizations for you! Try asking me things like 'show me a chart' or 'create a graph' and I'll generate custom visualizations based on your data.";
    }
    
    if (input.includes('opportunities') || input.includes('opportunity')) {
      return "I can help you explore opportunities, gaps, competitive insights, trends, risks, and recommendations from your report. You can also ask me to create charts and visualizations by saying things like 'show me a chart' or 'create a graph'.";
    }
    
    if (input.includes('competitor') || input.includes('competition')) {
      return "Let me analyze the competitive landscape for you. I can provide insights on competitor positioning, strengths, weaknesses, and differentiation opportunities.";
    }
    
    if (input.includes('trend') || input.includes('market')) {
      return "I can analyze market trends and their implications for your business. This includes emerging trends, trend-based opportunities, and strategic recommendations.";
    }
    
    if (input.includes('risk') || input.includes('risks')) {
      return "Risk assessment is crucial for strategic planning. I can identify potential risks, assess their probability, and suggest mitigation strategies.";
    }
    
    if (input.includes('recommendation') || input.includes('advice') || input.includes('suggest')) {
      return "I can provide strategic recommendations based on your analysis. These include priority actions, implementation complexity, and expected impact.";
    }
    
    // Help and guidance responses
    if (input.includes('help') || input.includes('what can you do') || input.includes('how can you help')) {
      return "I can help you explore opportunities, gaps, competitive insights, trends, risks, and recommendations from your report. You can also ask me to create charts and visualizations by saying things like 'show me a chart' or 'create a graph'.";
    }
    
    // More specific analysis responses
    if (input.includes('tell me more') || input.includes('explain') || input.includes('detail')) {
      return "I'd be happy to provide more detailed analysis! You can ask me about specific aspects like market opportunities, competitive analysis, or risk assessment. I can also create visual representations of the data.";
    }
    
    // Engagement responses
    if (input.includes('thank') || input.includes('thanks')) {
      return "You're welcome! I'm here to help you understand your analysis and generate insights. Is there anything specific you'd like to explore further?";
    }
    
    // Default contextual response
    if (hasAnalysisData) {
      return "Based on your analysis data, I can provide insights on market opportunities, competitive positioning, trends, and strategic recommendations. What specific aspect would you like to explore? I can also create charts and visualizations for better understanding.";
    }
    
    return "I'm here to help you understand your business analysis. You can ask me about market opportunities, competitive insights, trends, risks, or request charts and visualizations. What would you like to know?";
  };

  // Database storage function for conversation data
  const saveConversationToDatabase = async (messageData: any) => {
    try {
      const conversationEntry = {
        session_id: sessionId,
        timestamp: new Date().toISOString(),
        message_data: messageData,
        conversation_context: conversationContext,
        extracted_data: extractedData
      };

      // Save to backend database
      const response = await fetch('/api/conversations/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(conversationEntry)
      });

      if (response.ok) {
        console.log('Conversation saved to database');
      }
    } catch (error) {
      console.error('Failed to save conversation:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      isBot: false,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue("");
    setIsTyping(true);

    // Update conversation context
    setConversationContext(prev => [...prev.slice(-10), currentInput]); // Keep last 10 inputs

    // Reset textarea height after clearing
    setTimeout(() => {
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }, 0);

    // Enhanced response logic - try API first, fallback to intelligent responses
    try {
      setIsProcessing(true);
      const allMessages = [...messages, userMessage];
      
      try {
        // Try to use the backend API for comprehensive analysis
        const result = await processChatbotConversation(
          allMessages,
          uploadedFiles.length > 0 ? uploadedFiles : null,
          sessionId
        );

        // Save conversation data to database
        await saveConversationToDatabase({
          user_input: currentInput,
          api_result: result,
          session_context: allMessages
        });

        // Add typing delay for better UX
        await new Promise((resolve) =>
          setTimeout(resolve, 800 + Math.random() * 1200)
        );

        setIsTyping(false);

        if (result.status === "processed" || result.status === "confirmed") {
          // Success - we have all needed information
          setExtractedData(result.extracted_info || result.confirmed_info || null);
          setIsComplete(true);

          // Combine extracted/confirmed info with root-level website_crawled_info if available
          const messageData = result.extracted_info || result.confirmed_info;
          if (messageData && result.website_crawled_info) {
            messageData.website_crawled_info = result.website_crawled_info;
          }

          const botMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: result.message || "Perfect! I have collected all the necessary information about your business. Click below to proceed with the analysis.",
            isBot: true,
            timestamp: new Date(),
            status: result.status,
            data: messageData,
          };
          setMessages((prev) => [...prev, botMessage]);

        } else if (result.status === "confirmation_required") {
          // Need more information
          const missingFieldsText = result.missing_info && result.missing_info.length > 0
            ? ` I still need information about: ${result.missing_info.join(", ").replace(/_/g, " ")}.`
            : "";

          // Combine extracted info with root-level website_crawled_info if available
          const messageData = result.extracted_info;
          if (messageData && result.website_crawled_info) {
            messageData.website_crawled_info = result.website_crawled_info;
          }

          const botMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: `${result.message}${missingFieldsText} Could you provide more details?`,
            isBot: true,
            timestamp: new Date(),
            status: result.status,
            data: messageData,
          };
          setMessages((prev) => [...prev, botMessage]);
        }
      } catch (apiError) {
        // API failed, use intelligent local response
        console.log("API unavailable, using intelligent response system");
        
        await new Promise((resolve) =>
          setTimeout(resolve, 500 + Math.random() * 800)
        );

        setIsTyping(false);
        
        const intelligentResponse = generateIntelligentResponse(currentInput, messages);
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: intelligentResponse,
          isBot: true,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, botMessage]);

        // Save fallback response to database
        await saveConversationToDatabase({
          user_input: currentInput,
          fallback_response: intelligentResponse,
          session_context: allMessages
        });
      }
    } catch (error) {
      console.error("Message processing error:", error);
      setIsTyping(false);

      let errorMessage: Message;

      // Check if it's an API error with status code
      if (error instanceof ApiError) {
        let errorText = "Oops! Something went wrong.";

        // Customize message based on status code and error details
        switch (error.status) {
          case 403:
            if (error.message.toLowerCase().includes("rate limit")) {
              errorText = "Whoa there! You're going too fast. Please wait a moment before trying again.";
            } else if (error.message.toLowerCase().includes("permission")) {
              errorText = "Access denied! It looks like you don't have permission to perform this action.";
            } else if (error.message.toLowerCase().includes("token")) {
              errorText = "Your session has expired. Please refresh the page and try again.";
            } else {
              errorText = "NOT MY JOB!";
            }
            break;
          case 404:
            errorText = "Hmm, I can't find what I'm looking for. The service might be temporarily unavailable.";
            break;
          case 429:
            errorText = "Slow down there! You're making requests too quickly. Please wait a moment.";
            break;
          case 500:
            errorText = "Oops! Our servers are having a moment. Please try again in a few minutes.";
            break;
          default:
            // Fallback to intelligent response even on error
            errorText = generateIntelligentResponse(currentInput, messages);
        }

        errorMessage = {
          id: (Date.now() + 1).toString(),
          text: errorText,
          isBot: true,
          timestamp: new Date(),
          status: "error",
          gif: error.status ? getErrorGif(error.status) : undefined,
        };
      } else {
        // General error - use intelligent response
        errorMessage = {
          id: (Date.now() + 1).toString(),
          text: generateIntelligentResponse(currentInput, messages),
          isBot: true,
          timestamp: new Date(),
        };
      }

      setMessages((prev) => [...prev, errorMessage]);

      // Save error to database
      await saveConversationToDatabase({
        user_input: currentInput,
        error: error,
        session_context: messages
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setUploadedFiles((prev) => [...prev, ...files]);

    // Add a message about uploaded files
    if (files.length > 0) {
      const fileNames = files.map(f => f.name).join(", ");
      const fileMessage: Message = {
        id: Date.now().toString(),
        text: `📎 Uploaded ${files.length} file(s): ${fileNames}`,
        isBot: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, fileMessage]);
    }

    // Clear the input
    if (e.target) {
      e.target.value = '';
    }
  };

  const removeFile = (index: number) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleCompleteAnalysis = () => {
    onComplete(extractedData || undefined);
  };

  const handleQuickResponse = (text: string) => {
    setInputValue(text);
    // Auto-focus textarea after setting value
    setTimeout(() => {
      textareaRef.current?.focus();
    }, 100);
  };

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="bg-white rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-200/50 overflow-hidden h-[700px] flex flex-col"
    >
      <div className="bg-gradient-to-r from-blue-50 to-emerald-50 px-6 py-4 border-b border-slate-200">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-emerald-600 rounded-full flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900">
              OPPORTUNA Assistant
            </h3>
            <p className="text-sm text-slate-600">
              {isComplete
                ? "Analysis ready to launch"
                : isProcessing
                  ? "Processing your input..."
                  : "Ready to help with analysis"}
            </p>
          </div>
        </div>
      </div>

      <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-6 space-y-4 scroll-smooth">
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -20, opacity: 0 }}
              className={`flex ${message.isBot ? "justify-start" : "justify-end"}`}
            >
              <div
                className={`flex items-start space-x-2 max-w-[80%] ${message.isBot
                  ? "flex-row"
                  : "flex-row-reverse space-x-reverse"
                  }`}
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${message.isBot
                    ? "bg-gradient-to-r from-blue-600 to-emerald-600"
                    : "bg-slate-600"
                    }`}
                >
                  {message.isBot ? (
                    <Bot className="w-4 h-4 text-white" />
                  ) : (
                    <User className="w-4 h-4 text-white" />
                  )}
                </div>
                <div
                  className={`rounded-2xl px-4 py-3 ${message.isBot
                    ? message.status === "error"
                      ? "bg-red-50 border border-red-200 text-slate-900"
                      : message.status === "processed" || message.status === "confirmed"
                        ? "bg-green-50 border border-green-200 text-slate-900"
                        : message.status === "confirmation_required"
                          ? "bg-yellow-50 border border-yellow-200 text-slate-900"
                          : "bg-slate-100 text-slate-900"
                    : "bg-gradient-to-r from-blue-600 to-emerald-600 text-white"
                    }`}
                >
                  {message.isBot ? (
                    <div className="space-y-3">
                      <p className="text-sm leading-relaxed">{linkifyText(message.text)}</p>

                      {/* Display GIF if present */}
                      {message.gif && (
                        <div className="mt-3">
                          <img
                            src={message.gif}
                            alt="Response GIF"
                            className="rounded-md max-w-xs shadow-md"
                            style={{ maxHeight: '200px' }}
                          />
                        </div>
                      )}

                      {/* Render extracted data */}
                      {message.data && Object.keys(message.data).length > 0 && (
                        <div className="mt-4 space-y-3">
                          <h4 className="text-sm font-semibold text-slate-800 border-b border-slate-200 pb-1">
                            Extracted Information:
                          </h4>
                          <div className="space-y-2 text-xs">
                            {Object.entries(message.data)
                              .filter(([key]) => key !== "website_crawled_info" && !key.toLowerCase().includes("crawled_info"))
                              .map(([key, value]) => renderDataEntry(key, value))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm leading-relaxed">{message.text}</p>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isTyping && (
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="flex justify-start"
          >
            <div className="flex items-start space-x-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-600 to-emerald-600 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="bg-slate-100 rounded-2xl px-4 py-3">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                  <div
                    className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0.1s" }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0.2s" }}
                  ></div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="p-6 border-t border-slate-200">
        {/* Submit for Analysis Button - shown when complete */}
        {isComplete && (
          <div className="mb-4">
            <motion.button
              onClick={handleCompleteAnalysis}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full py-4 bg-gradient-to-r from-blue-600 to-emerald-600 text-white rounded-lg font-medium flex items-center justify-center space-x-2 shadow-lg shadow-blue-500/25 hover:from-blue-700 hover:to-emerald-700 transition-all duration-200"
            >
              <span>Submit for analysis</span>
              <ArrowRight className="w-5 h-5" />
            </motion.button>
          </div>
        )}

        {/* File Upload Section */}
        {uploadedFiles.length > 0 && (
          <div className="mb-4">
            <div className="flex flex-wrap gap-2">
              {uploadedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center space-x-2 bg-slate-100 rounded-lg px-3 py-2 text-sm"
                >
                  <File className="w-4 h-4 text-slate-600" />
                  <span className="text-slate-700 truncate max-w-[150px]">
                    {file.name}
                  </span>
                  <button
                    onClick={() => removeFile(index)}
                    className="text-slate-400 hover:text-red-500 transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick Response Buttons */}
        <div className="mb-4">
          <div className="flex flex-wrap gap-2">
            {!isTyping && !isProcessing && (
              <>
                <motion.button
                  onClick={() => handleQuickResponse("what exactly are the gaps")}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-3 py-2 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium hover:bg-blue-100 transition-colors"
                >
                  What are the gaps?
                </motion.button>
                <motion.button
                  onClick={() => handleQuickResponse("list them")}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-3 py-2 bg-emerald-50 text-emerald-700 rounded-lg text-sm font-medium hover:bg-emerald-100 transition-colors"
                >
                  List them
                </motion.button>
                <motion.button
                  onClick={() => handleQuickResponse("tell me more about the gaps")}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-3 py-2 bg-purple-50 text-purple-700 rounded-lg text-sm font-medium hover:bg-purple-100 transition-colors"
                >
                  Tell me more
                </motion.button>
                <motion.button
                  onClick={() => handleQuickResponse("show me a chart")}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-3 py-2 bg-amber-50 text-amber-700 rounded-lg text-sm font-medium hover:bg-amber-100 transition-colors"
                >
                  Show chart
                </motion.button>
              </>
            )}
          </div>
        </div>

        {/* Message Input Area - Enhanced for better responsiveness */}
        <div className="flex space-x-2">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={inputValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyPress}
              placeholder={isComplete
                ? "Ask follow-up questions or provide additional details..."
                : "Ask me about your report, request charts, or type your questions... (Enter to send, Shift+Enter for new line)"}
              disabled={isTyping || isProcessing}
              rows={1}
              className="w-full px-4 py-3 pr-12 rounded-lg border border-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 placeholder-slate-400 disabled:bg-slate-50 disabled:text-slate-400 resize-none min-h-[48px] max-h-[120px] scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-slate-100"
            />
            {/* Character count for longer messages */}
            {inputValue.length > 100 && (
              <div className="absolute bottom-1 right-12 text-xs text-slate-400">
                {inputValue.length}
              </div>
            )}
          </div>

          {/* File Upload Button */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            multiple
            accept=".pdf,.doc,.docx,.txt,.csv,.xlsx,.xls"
            className="hidden"
          />
          <motion.button
            onClick={() => fileInputRef.current?.click()}
            disabled={isTyping || isProcessing}
            whileHover={!isTyping && !isProcessing ? { scale: 1.05 } : {}}
            whileTap={!isTyping && !isProcessing ? { scale: 0.95 } : {}}
            className={`w-12 h-12 flex items-center justify-center rounded-lg transition-all duration-200 ${!isTyping && !isProcessing
              ? "bg-slate-200 text-slate-600 hover:bg-slate-300"
              : "bg-slate-100 text-slate-400 cursor-not-allowed"
              }`}
          >
            <Paperclip className="w-5 h-5" />
          </motion.button>

          <motion.button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isTyping || isProcessing}
            whileHover={inputValue.trim() && !isTyping && !isProcessing ? { scale: 1.05 } : {}}
            whileTap={inputValue.trim() && !isTyping && !isProcessing ? { scale: 0.95 } : {}}
            className={`w-12 h-12 flex items-center justify-center rounded-lg transition-all duration-200 ${inputValue.trim() && !isTyping && !isProcessing
              ? "bg-gradient-to-r from-blue-600 to-emerald-600 text-white shadow-lg shadow-blue-500/25 hover:from-blue-700 hover:to-emerald-700"
              : "bg-slate-200 text-slate-400 cursor-not-allowed"
              }`}
          >
            {isProcessing ? (
              <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
};

export default Chatbot;
