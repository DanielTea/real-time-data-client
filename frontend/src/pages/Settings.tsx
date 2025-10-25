import React, { useState, useEffect } from "react";

export const Settings: React.FC = () => {
    const [wsUrl, setWsUrl] = useState("ws://localhost:8080");
    const [alpacaKey, setAlpacaKey] = useState("");
    const [alpacaSecret, setAlpacaSecret] = useState("");
    const [claudeKey, setClaudeKey] = useState("");
    const [deepseekKey, setDeepseekKey] = useState("");
    const [aiModel, setAiModel] = useState<"claude" | "deepseek">("claude");
    const [paperMode, setPaperMode] = useState(true);
    const [saveStatus, setSaveStatus] = useState("");

    // Load settings from localStorage
    useEffect(() => {
        const savedAlpacaKey = localStorage.getItem("alpaca_key") || "";
        const savedAlpacaSecret = localStorage.getItem("alpaca_secret") || "";
        const savedClaudeKey = localStorage.getItem("claude_key") || "";
        const savedDeepseekKey = localStorage.getItem("deepseek_key") || "";
        const savedAiModel =
            (localStorage.getItem("ai_model") as "claude" | "deepseek") || "claude";
        const savedPaperMode = localStorage.getItem("paper_mode") === "true";

        setAlpacaKey(savedAlpacaKey);
        setAlpacaSecret(savedAlpacaSecret);
        setClaudeKey(savedClaudeKey);
        setDeepseekKey(savedDeepseekKey);
        setAiModel(savedAiModel);
        setPaperMode(savedPaperMode);
    }, []);

    const handleSaveApiKeys = () => {
        localStorage.setItem("alpaca_key", alpacaKey);
        localStorage.setItem("alpaca_secret", alpacaSecret);
        localStorage.setItem("claude_key", claudeKey);
        localStorage.setItem("deepseek_key", deepseekKey);
        localStorage.setItem("ai_model", aiModel);
        localStorage.setItem("paper_mode", paperMode.toString());

        setSaveStatus("✓ Settings saved successfully!");
        setTimeout(() => setSaveStatus(""), 3000);
    };

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Settings</h1>
                <p className="text-gray-600">
                    Configure your Polymarket dashboard and trading preferences
                </p>
            </div>

            <div className="max-w-2xl space-y-6">
                {/* Trading API Configuration */}
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">
                        🔐 Trading API Configuration
                    </h2>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Alpaca API Key
                            </label>
                            <input
                                type="password"
                                value={alpacaKey}
                                onChange={e => setAlpacaKey(e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                                placeholder="Enter your Alpaca API key"
                            />
                            <p className="mt-1 text-xs text-gray-500">
                                Get your API key from{" "}
                                <a
                                    href="https://alpaca.markets/"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:underline"
                                >
                                    Alpaca Markets
                                </a>
                            </p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Alpaca Secret Key
                            </label>
                            <input
                                type="password"
                                value={alpacaSecret}
                                onChange={e => setAlpacaSecret(e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                                placeholder="Enter your Alpaca secret key"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                🤖 AI Model Selection
                            </label>
                            <select
                                value={aiModel}
                                onChange={e => setAiModel(e.target.value as "claude" | "deepseek")}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                            >
                                <option value="claude">Claude 3.5 Sonnet (Anthropic)</option>
                                <option value="deepseek">DeepSeek-V3.2-Exp (Reasoning)</option>
                            </select>
                            <p className="mt-1 text-xs text-gray-500">
                                Choose which AI model to use for trading decisions
                            </p>
                        </div>

                        {aiModel === "claude" && (
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Anthropic (Claude) API Key
                                </label>
                                <input
                                    type="password"
                                    value={claudeKey}
                                    onChange={e => setClaudeKey(e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                                    placeholder="Enter your Claude API key"
                                />
                                <p className="mt-1 text-xs text-gray-500">
                                    Get your API key from{" "}
                                    <a
                                        href="https://console.anthropic.com/"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-600 hover:underline"
                                    >
                                        Anthropic Console
                                    </a>
                                </p>
                            </div>
                        )}

                        {aiModel === "deepseek" && (
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    DeepSeek API Key
                                </label>
                                <input
                                    type="password"
                                    value={deepseekKey}
                                    onChange={e => setDeepseekKey(e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                                    placeholder="Enter your DeepSeek API key"
                                />
                                <p className="mt-1 text-xs text-gray-500">
                                    Get your API key from{" "}
                                    <a
                                        href="https://platform.deepseek.com/api_keys"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-600 hover:underline"
                                    >
                                        DeepSeek Platform
                                    </a>{" "}
                                    ($0.55/M tokens - much cheaper!)
                                </p>
                            </div>
                        )}

                        <div className="flex items-center justify-between pt-2">
                            <div>
                                <div className="text-sm font-medium text-gray-700">
                                    Paper Trading Mode
                                </div>
                                <div className="text-xs text-gray-500">
                                    Use paper trading (no real money)
                                </div>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input
                                    type="checkbox"
                                    className="sr-only peer"
                                    checked={paperMode}
                                    onChange={e => setPaperMode(e.target.checked)}
                                />
                                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
                            </label>
                        </div>

                        <div className="pt-2">
                            <button
                                onClick={handleSaveApiKeys}
                                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                            >
                                💾 Save API Keys
                            </button>
                            {saveStatus && (
                                <span className="ml-3 text-sm text-green-600">{saveStatus}</span>
                            )}
                        </div>

                        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                            <p className="text-xs text-yellow-800">
                                ⚠️ <strong>Security Notice:</strong> API keys are stored in your
                                browser's local storage. Never share your keys with anyone.
                            </p>
                        </div>
                    </div>
                </div>

                {/* WebSocket Configuration */}
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">WebSocket Server</h2>
                    <div className="space-y-3">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Server URL
                            </label>
                            <input
                                type="text"
                                value={wsUrl}
                                onChange={e => setWsUrl(e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                                placeholder="ws://localhost:8080"
                            />
                            <p className="mt-1 text-xs text-gray-500">Current server: {wsUrl}</p>
                        </div>
                    </div>
                </div>

                {/* Cache Management */}
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">
                        Database Management
                    </h2>
                    <div className="space-y-3">
                        <p className="text-sm text-gray-600">
                            <strong>Purge Database:</strong> Force delete the IndexedDB cache and
                            reload the page. Use this to clear all stored market data. The cache
                            will be rebuilt automatically as new data arrives.
                        </p>
                        <button
                            onClick={() => {
                                if (
                                    confirm(
                                        "Purge the database? This will remove all cached markets and reload the page.",
                                    )
                                ) {
                                    console.log("[Settings] Purging IndexedDB...");
                                    // Force delete without async - immediate action
                                    indexedDB.deleteDatabase("PolymarketCache");
                                    alert("Database purged! Reloading page...");
                                    // Force hard reload
                                    setTimeout(() => window.location.reload(true), 100);
                                }
                            }}
                            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
                        >
                            🔥 Purge Database
                        </button>
                    </div>
                </div>

                {/* Display Preferences */}
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">
                        Display Preferences
                    </h2>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="text-sm font-medium text-gray-700">Show Deltas</div>
                                <div className="text-xs text-gray-500">
                                    Display probability changes
                                </div>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input type="checkbox" className="sr-only peer" defaultChecked />
                                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                            </label>
                        </div>

                        <div className="flex items-center justify-between">
                            <div>
                                <div className="text-sm font-medium text-gray-700">
                                    Auto-refresh
                                </div>
                                <div className="text-xs text-gray-500">
                                    Automatically update markets
                                </div>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input type="checkbox" className="sr-only peer" defaultChecked />
                                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                            </label>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
