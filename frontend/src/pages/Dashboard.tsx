import React, { useState, useMemo } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import { MarketCard } from "../components/MarketCard";
import { ConnectionStatus } from "../components/ConnectionStatus";

export const Dashboard: React.FC = () => {
    // Connect to the backend WebSocket server
    const { isConnected, pages, error } = useWebSocket("ws://localhost:8080");
    const [selectedCategory, setSelectedCategory] = useState("All");
    const [searchKeyword, setSearchKeyword] = useState("");

    // Get all markets from all pages
    const allMarkets = pages.flatMap(page => page.markets);

    // Dynamically extract unique categories from current markets
    const categories = useMemo(() => {
        const categoryMap = new Map<string, number>();
        allMarkets.forEach(market => {
            const category = market.category || "Uncategorized";
            categoryMap.set(category, (categoryMap.get(category) || 0) + 1);
        });

        // Sort by count (descending)
        const sortedCategories = Array.from(categoryMap.entries())
            .sort(([, a], [, b]) => b - a)
            .map(([category, count]) => ({ category, count }));

        // Add "All" at the beginning
        return [{ category: "All", count: allMarkets.length }, ...sortedCategories];
    }, [allMarkets]);

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

        // Keyword filter (search in title, outcome, and description)
        let keywordMatch = true;
        if (searchKeyword.trim()) {
            const keyword = searchKeyword.toLowerCase();
            const titleMatch = market.title.toLowerCase().includes(keyword);
            const outcomeMatch = market.outcome.toLowerCase().includes(keyword);
            const descriptionMatch = market.description?.toLowerCase().includes(keyword) || false;
            keywordMatch = titleMatch || outcomeMatch || descriptionMatch;
        }

        return categoryMatch && keywordMatch;
    });

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                    Real-Time Probability Changes
                </h1>
                <p className="text-gray-600">
                    Live updates showing all probability changes across Polymarket markets
                </p>
            </div>

            <ConnectionStatus isConnected={isConnected} error={error} />

            {/* Category Filter */}
            <div className="mb-6">
                <p className="text-sm font-medium text-gray-700 mb-2">
                    Filter by Category ({categories.length} categories):
                </p>
                <div className="flex gap-2 flex-wrap">
                    {categories.map(({ category, count }) => (
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
                        <div className="text-gray-500">
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
    );
};
