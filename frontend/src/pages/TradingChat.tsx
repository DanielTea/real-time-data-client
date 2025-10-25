import React, { useState, useEffect, useRef } from "react";

interface Message {
    role: "user" | "assistant";
    content: string;
    timestamp: Date;
}

interface AccountInfo {
    status?: string;
    cash?: number;
    portfolio_value?: number;
    buying_power?: number;
    equity?: number;
}

export const TradingChat: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isInitialized, setIsInitialized] = useState(false);
    const [accountInfo, setAccountInfo] = useState<AccountInfo | null>(null);
    const [brokerInfo, setBrokerInfo] = useState<{broker: string, supports_leverage: boolean, max_leverage: number} | null>(null);
    const [serverUrl] = useState("http://localhost:5002"); // Updated to new multi-broker server
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when new messages arrive
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Initialize the trading server on mount
    useEffect(() => {
        initializeServer();
    }, []);

    const initializeServer = async () => {
        const broker = localStorage.getItem("broker") || "alpaca";
        const brokerKey = localStorage.getItem(`${broker}_key`);
        const brokerSecret = localStorage.getItem(`${broker}_secret`);
        const claudeKey = localStorage.getItem("claude_key");
        const deepseekKey = localStorage.getItem("deepseek_key");
        const aiModel = localStorage.getItem("ai_model") || "claude";
        const paperMode = localStorage.getItem("paper_mode") === "true";

        // Validate broker API keys
        if (!brokerKey || !brokerSecret) {
            setMessages([
                {
                    role: "assistant",
                    content:
                        `⚠️ Please configure your ${broker.charAt(0).toUpperCase() + broker.slice(1)} API keys in Settings before using the trading chat.`,
                    timestamp: new Date(),
                },
            ]);
            return;
        }

        if (aiModel === "claude" && !claudeKey) {
            setMessages([
                {
                    role: "assistant",
                    content:
                        "⚠️ Please configure your Claude API key in Settings or switch to DeepSeek.",
                    timestamp: new Date(),
                },
            ]);
            return;
        }

        if (aiModel === "deepseek" && !deepseekKey) {
            setMessages([
                {
                    role: "assistant",
                    content:
                        "⚠️ Please configure your DeepSeek API key in Settings or switch to Claude.",
                    timestamp: new Date(),
                },
            ]);
            return;
        }

        try {
            const requestBody: any = {
                broker: broker,
                claude_key: claudeKey,
                deepseek_key: deepseekKey,
                ai_model: aiModel,
                paper_mode: paperMode,
            };
            
            // Add broker-specific keys
            requestBody[`${broker}_key`] = brokerKey;
            requestBody[`${broker}_secret`] = brokerSecret;
            
            const response = await fetch(`${serverUrl}/api/initialize`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(requestBody),
            });

            if (response.ok) {
                const data = await response.json();
                const modelName =
                    data.ai_model === "deepseek" ? "DeepSeek-V3.2-Exp" : "Claude 3.5 Sonnet";
                const brokerName = data.broker || broker;
                const supportsLeverage = data.supports_leverage || false;
                const maxLeverage = data.max_crypto_leverage || 1;
                
                setBrokerInfo({
                    broker: brokerName,
                    supports_leverage: supportsLeverage,
                    max_leverage: maxLeverage
                });
                
                setIsInitialized(true);
                
                let leverageInfo = "";
                if (supportsLeverage) {
                    leverageInfo = ` 🚀 Leverage trading enabled (up to ${maxLeverage}x on crypto)!`;
                }
                
                setMessages([
                    {
                        role: "assistant",
                        content: `✅ Trading chat initialized with ${brokerName} broker using ${modelName} in ${paperMode ? "PAPER" : "LIVE"} mode.${leverageInfo}\n\nYou can now execute trades! Try:\n• "buy $100 of BTC${supportsLeverage ? ' with 10x leverage' : ''}"\n• "show my account balance"\n• "what positions do I have?"`,
                        timestamp: new Date(),
                    },
                ]);

                // Fetch account info
                fetchAccountInfo();
            } else {
                const error = await response.json();
                setMessages([
                    {
                        role: "assistant",
                        content: `❌ Failed to initialize: ${error.error}. Please check your API keys in Settings.`,
                        timestamp: new Date(),
                    },
                ]);
            }
        } catch (error) {
            setMessages([
                {
                    role: "assistant",
                    content: `❌ Cannot connect to trading server at ${serverUrl}. Please make sure the server is running.`,
                    timestamp: new Date(),
                },
            ]);
        }
    };

    const fetchAccountInfo = async () => {
        try {
            const response = await fetch(`${serverUrl}/api/account`);
            if (response.ok) {
                const data = await response.json();
                setAccountInfo(data);
            }
        } catch (error) {
            console.error("Failed to fetch account info:", error);
        }
    };

    const handleSendMessage = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            role: "user",
            content: input,
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInput("");
        setIsLoading(true);

        try {
            // Build conversation history for Claude
            const history = messages.map(msg => ({
                role: msg.role,
                content: msg.content,
            }));

            const response = await fetch(`${serverUrl}/api/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    message: input,
                    history: history,
                }),
            });

            if (response.ok) {
                const data = await response.json();
                const assistantMessage: Message = {
                    role: "assistant",
                    content: data.response,
                    timestamp: new Date(),
                };
                setMessages(prev => [...prev, assistantMessage]);

                // Refresh account info after trading commands
                fetchAccountInfo();
            } else {
                const error = await response.json();
                const errorMessage: Message = {
                    role: "assistant",
                    content: `❌ Error: ${error.error}`,
                    timestamp: new Date(),
                };
                setMessages(prev => [...prev, errorMessage]);
            }
        } catch (error) {
            const errorMessage: Message = {
                role: "assistant",
                content: `❌ Failed to send message: ${error}`,
                timestamp: new Date(),
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    return (
        <div className="container mx-auto px-4 py-8 h-full flex flex-col">
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">💬 Trading Chat</h1>
                <p className="text-gray-600">
                    Chat with AI to execute trades{brokerInfo ? ` on ${brokerInfo.broker}` : ''}
                    {brokerInfo?.supports_leverage && (
                        <span className="ml-2 px-2 py-1 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs rounded-full font-semibold">
                            ⚡ {brokerInfo.max_leverage}x LEVERAGE
                        </span>
                    )}
                </p>
            </div>

            {/* Account Info Banner */}
            {accountInfo && (
                <div className="mb-4 bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                            <div className="text-gray-600 text-xs">Portfolio Value</div>
                            <div className="text-lg font-semibold text-gray-900">
                                ${(accountInfo.portfolio_value || accountInfo.equity || 0).toFixed(2)}
                            </div>
                        </div>
                        <div>
                            <div className="text-gray-600 text-xs">Cash</div>
                            <div className="text-lg font-semibold text-gray-900">
                                ${(accountInfo.cash || 0).toFixed(2)}
                            </div>
                        </div>
                        <div>
                            <div className="text-gray-600 text-xs">Buying Power</div>
                            <div className="text-lg font-semibold text-gray-900">
                                ${(accountInfo.buying_power || 0).toFixed(2)}
                            </div>
                        </div>
                        <div>
                            <div className="text-gray-600 text-xs">Status</div>
                            <div className="text-lg font-semibold text-green-600">
                                {(accountInfo.status || 'ACTIVE').toUpperCase()}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Chat Container */}
            <div className="flex-1 bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col overflow-hidden">
                {/* Messages Area */}
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    {messages.map((message, index) => (
                        <div
                            key={index}
                            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                            <div
                                className={`max-w-[80%] rounded-lg px-4 py-3 ${
                                    message.role === "user"
                                        ? "bg-blue-600 text-white"
                                        : "bg-gray-100 text-gray-900"
                                }`}
                            >
                                <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                                <div
                                    className={`text-xs mt-1 ${
                                        message.role === "user" ? "text-blue-200" : "text-gray-500"
                                    }`}
                                >
                                    {message.timestamp.toLocaleTimeString()}
                                </div>
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex justify-start">
                            <div className="bg-gray-100 rounded-lg px-4 py-3">
                                <div className="flex space-x-2">
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                    <div
                                        className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                                        style={{ animationDelay: "0.2s" }}
                                    ></div>
                                    <div
                                        className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                                        style={{ animationDelay: "0.4s" }}
                                    ></div>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="border-t border-gray-200 p-4">
                    <div className="flex space-x-2">
                        <input
                            type="text"
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            disabled={!isInitialized || isLoading}
                            placeholder={
                                isInitialized
                                    ? "Type a trading command... (e.g., 'buy $100 of BTC')"
                                    : "Initializing..."
                            }
                            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                        />
                        <button
                            onClick={handleSendMessage}
                            disabled={!isInitialized || isLoading || !input.trim()}
                            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed font-medium"
                        >
                            {isLoading ? "..." : "Send"}
                        </button>
                    </div>
                    <div className="mt-2 text-xs text-gray-500">
                        💡 Try: {brokerInfo?.supports_leverage 
                            ? '"buy $50 of BTC with 10x leverage", "short ETH at 5x", "show positions"'
                            : '"buy $50 of ETH", "show my positions", "what\'s the BTC price?"'
                        }
                    </div>
                </div>
            </div>
        </div>
    );
};
