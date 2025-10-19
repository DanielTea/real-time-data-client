import React, { useState } from "react";
import { useWebSocket } from "./hooks/useWebSocket";
import { MarketCard } from "./components/MarketCard";
import { ConnectionStatus } from "./components/ConnectionStatus";
import { deleteDatabase } from "./db/marketDb";

const CATEGORIES = [
    "All",
    "Trending",
    "Breaking",
    "New",
    "Politics",
    "Sports",
    "Finance",
    "Crypto",
    "Geopolitics",
    "Earnings",
    "Tech",
    "Culture",
    "World",
    "Economy",
    "Elections",
    "Mentions",
];

function App() {
    // Connect to the backend WebSocket server
    const { isConnected, pages, error } = useWebSocket("ws://localhost:8080");
    const [selectedCategory, setSelectedCategory] = useState("All");
    const [searchKeyword, setSearchKeyword] = useState("");

    // Get all markets from all pages
    const allMarkets = pages.flatMap(page => page.markets);

    // Filter markets by category and keyword
    const filteredMarkets = allMarkets.filter(market => {
        // Category filter
        let categoryMatch = true;
        if (selectedCategory !== "All") {
            if (market.category) {
                categoryMatch = market.category.toLowerCase() === selectedCategory.toLowerCase();
            } else {
                const title = market.title.toLowerCase();
                categoryMatch = title.includes(selectedCategory.toLowerCase());
            }
        }

        // Keyword filter
        let keywordMatch = true;
        if (searchKeyword.trim()) {
            const keyword = searchKeyword.toLowerCase();
            const titleMatch = market.title.toLowerCase().includes(keyword);
            const outcomeMatch = market.outcome.toLowerCase().includes(keyword);
            keywordMatch = titleMatch || outcomeMatch;
        }

        return categoryMatch && keywordMatch;
    });

    const handleClearCache = async () => {
        if (
            confirm(
                "Are you sure you want to clear the cache? This will remove all stored markets.",
            )
        ) {
            try {
                await deleteDatabase();
                window.location.reload();
            } catch (err) {
                console.error("Failed to clear cache:", err);
                alert("Failed to clear cache. Check console for details.");
            }
        }
    };

    return (
        <div
            className="min-h-screen bg-gray-50"
            style={{ minHeight: "100vh", backgroundColor: "#f9fafb" }}
        >
            <div className="container mx-auto px-4 py-8">
                <div className="mb-8 flex items-center justify-between">
                    <div>
                        <h1
                            className="text-3xl font-bold text-gray-900 mb-2"
                            style={{ color: "#111827", fontSize: "1.875rem", fontWeight: 700 }}
                        >
                            Polymarket Real-Time Probability Changes
                        </h1>
                        <p className="text-gray-600">
                            Live updates showing all probability changes across Polymarket markets
                        </p>
                    </div>
                    <button
                        onClick={handleClearCache}
                        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
                    >
                        Clear Cache
                    </button>
                </div>

                <ConnectionStatus isConnected={isConnected} error={error} />

                {/* Category Filter */}
                <div className="mb-6">
                    <p className="text-sm font-medium text-gray-700 mb-2">Filter by Category:</p>
                    <div className="flex gap-2 flex-wrap">
                        {CATEGORIES.map(category => (
                            <button
                                key={category}
                                onClick={() => {
                                    setSelectedCategory(category);
                                }}
                                className={`px-3 py-1 rounded-full font-medium transition-colors text-sm ${
                                    selectedCategory === category
                                        ? "bg-blue-600 text-white"
                                        : "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50"
                                }`}
                            >
                                {category}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Keyword Search Filter */}
                <div className="mb-6">
                    <p className="text-sm font-medium text-gray-700 mb-2">Search by Keyword:</p>
                    <input
                        type="text"
                        placeholder="Search market title or outcome..."
                        value={searchKeyword}
                        onChange={e => setSearchKeyword(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                </div>

                {/* Results Info */}
                <div className="mb-4 text-sm text-gray-600">
                    Showing {filteredMarkets.length} market{filteredMarkets.length !== 1 ? "s" : ""}
                    {selectedCategory !== "All" && ` (filtered by ${selectedCategory})`}
                    {searchKeyword && ` (matching "${searchKeyword}")`}
                </div>

                {/* Markets Grid - All on one page */}
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {filteredMarkets.length === 0 ? (
                        <div className="col-span-full text-center py-12">
                            <div
                                className="text-gray-500"
                                style={{ color: "#6b7280", fontSize: "1rem" }}
                            >
                                {isConnected
                                    ? `No markets found for "${selectedCategory}"${searchKeyword ? ` matching "${searchKeyword}"` : ""}`
                                    : "Connecting..."}
                            </div>
                        </div>
                    ) : (
                        filteredMarkets.map((market, index) => (
                            <MarketCard
                                key={`${market.title}-${market.outcome}-${index}`}
                                market={market}
                            />
                        ))
                    )}
                </div>

                {filteredMarkets.length > 0 && (
                    <div className="mt-8 text-center text-sm text-gray-500">
                        Displaying {filteredMarkets.length} market
                        {filteredMarkets.length !== 1 ? "s" : ""}
                    </div>
                )}
            </div>
        </div>
    );
}

export default App;
