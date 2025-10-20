import React, { useState, useMemo } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import { ConnectionStatus } from "../components/ConnectionStatus";

export const JsonView: React.FC = () => {
    const { isConnected, pages, error } = useWebSocket("ws://localhost:8080");
    const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
    const [searchKeyword, setSearchKeyword] = useState("");

    // Get all markets from all pages
    const allMarkets = pages.flatMap(page => page.markets);

    // Dynamically extract unique categories from current markets
    const availableCategories = useMemo(() => {
        const categoryMap = new Map<string, number>();
        allMarkets.forEach(market => {
            const category = market.category || "Uncategorized";
            categoryMap.set(category, (categoryMap.get(category) || 0) + 1);
        });

        // Sort by count (descending)
        return Array.from(categoryMap.entries())
            .sort(([, a], [, b]) => b - a)
            .map(([category, count]) => ({ category, count }));
    }, [allMarkets]);

    // Filter markets by categories and keyword
    const filteredMarkets = useMemo(() => {
        return allMarkets.filter(market => {
            // Category filter
            let categoryMatch = true;
            if (selectedCategories.length > 0) {
                if (market.category) {
                    categoryMatch = selectedCategories.some(
                        cat => cat.toLowerCase() === market.category?.toLowerCase(),
                    );
                } else {
                    const title = market.title.toLowerCase();
                    categoryMatch = selectedCategories.some(cat =>
                        title.includes(cat.toLowerCase()),
                    );
                }
            }

            // Keyword filter (search in title, outcome, and description)
            let keywordMatch = true;
            if (searchKeyword.trim()) {
                const keyword = searchKeyword.toLowerCase();
                const titleMatch = market.title.toLowerCase().includes(keyword);
                const outcomeMatch = market.outcome.toLowerCase().includes(keyword);
                const descriptionMatch =
                    market.description?.toLowerCase().includes(keyword) || false;
                keywordMatch = titleMatch || outcomeMatch || descriptionMatch;
            }

            return categoryMatch && keywordMatch;
        });
    }, [allMarkets, selectedCategories, searchKeyword]);

    const toggleCategory = (category: string) => {
        setSelectedCategories(prev => {
            if (prev.includes(category)) {
                return prev.filter(c => c !== category);
            } else {
                return [...prev, category];
            }
        });
    };

    const selectAllCategories = () => {
        setSelectedCategories(availableCategories.map(c => c.category));
    };

    const clearAllCategories = () => {
        setSelectedCategories([]);
    };

    // Format JSON with pretty print
    const jsonOutput = JSON.stringify(filteredMarkets, null, 2);

    const copyToClipboard = () => {
        navigator.clipboard.writeText(jsonOutput);
        alert("JSON copied to clipboard!");
    };

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">JSON View</h1>
                <p className="text-gray-600">Real-time market data in JSON format with filtering</p>
            </div>

            <ConnectionStatus isConnected={isConnected} error={error} />

            {/* Category Filter */}
            <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-medium text-gray-700">
                        Select Categories ({selectedCategories.length} of{" "}
                        {availableCategories.length} selected):
                    </p>
                    <div className="flex gap-2">
                        <button
                            onClick={selectAllCategories}
                            className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                        >
                            Select All ({availableCategories.length})
                        </button>
                        <button
                            onClick={clearAllCategories}
                            className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                        >
                            Clear All
                        </button>
                    </div>
                </div>
                <div className="flex gap-2 flex-wrap">
                    {availableCategories.map(({ category, count }) => (
                        <button
                            key={category}
                            onClick={() => toggleCategory(category)}
                            className={`px-3 py-1 rounded-full font-medium transition-colors text-sm ${
                                selectedCategories.includes(category)
                                    ? "bg-blue-600 text-white"
                                    : "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50"
                            }`}
                        >
                            {category} <span className="text-xs opacity-75">({count})</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Keyword Search Filter */}
            <div className="mb-6">
                <p className="text-sm font-medium text-gray-700 mb-2">Search by Keyword:</p>
                <input
                    type="text"
                    placeholder="Search market title, outcome, or description..."
                    value={searchKeyword}
                    onChange={e => setSearchKeyword(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                />
            </div>

            {/* Results Info and Actions */}
            <div className="mb-4 flex items-center justify-between">
                <div className="text-sm text-gray-600">
                    Showing {filteredMarkets.length} market{filteredMarkets.length !== 1 ? "s" : ""}
                    {selectedCategories.length > 0 &&
                        ` (filtered by ${selectedCategories.length} ${selectedCategories.length === 1 ? "category" : "categories"})`}
                    {searchKeyword && ` (matching "${searchKeyword}")`}
                </div>
                <button
                    onClick={copyToClipboard}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
                >
                    📋 Copy JSON
                </button>
            </div>

            {/* JSON Output */}
            <div className="bg-gray-900 rounded-lg p-4 overflow-auto">
                <pre className="text-green-400 text-sm font-mono whitespace-pre-wrap break-words">
                    {filteredMarkets.length === 0 ? (
                        <span className="text-gray-500">
                            {isConnected
                                ? `No markets found${selectedCategories.length > 0 ? " for selected categories" : ""}${searchKeyword ? ` matching "${searchKeyword}"` : ""}`
                                : "Connecting..."}
                        </span>
                    ) : (
                        jsonOutput
                    )}
                </pre>
            </div>

            {filteredMarkets.length > 0 && (
                <div className="mt-4 text-center text-sm text-gray-500">
                    Total: {filteredMarkets.length} market
                    {filteredMarkets.length !== 1 ? "s" : ""} • JSON Size:{" "}
                    {(new Blob([jsonOutput]).size / 1024).toFixed(2)} KB
                </div>
            )}
        </div>
    );
};
