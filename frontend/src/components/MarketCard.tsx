import React from "react";
import type { MarketData } from "../types";

interface MarketCardProps {
    market: MarketData;
}

export const MarketCard: React.FC<MarketCardProps> = ({ market }) => {
    const formatDelta = (delta?: number) => {
        if (delta === undefined) return "first occurrence";
        const sign = delta >= 0 ? "+" : "";
        return `${sign}${delta.toFixed(1)}%`;
    };

    const getDeltaColor = (delta?: number) => {
        if (delta === undefined) return "text-gray-500";
        if (delta > 0) return "text-green-500";
        if (delta < 0) return "text-red-500";
        return "text-gray-500";
    };

    const getSideColor = (side: "BUY" | "SELL") => {
        return side === "BUY" ? "text-green-600" : "text-red-600";
    };

    const formatTime = (timestamp: number | undefined) => {
        if (!timestamp) return "unknown time";

        try {
            const date = new Date(timestamp);
            if (isNaN(date.getTime())) {
                return "unknown time";
            }
            return date.toLocaleTimeString();
        } catch (e) {
            return "unknown time";
        }
    };

    return (
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500 hover:shadow-lg transition-shadow flex flex-col items-center justify-center min-h-48 relative group cursor-pointer">
            {/* Background link layer */}
            {market.marketUrl && (
                <a
                    href={market.marketUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="absolute inset-0 rounded-lg z-10"
                    title="Open market on Polymarket"
                />
            )}

            {/* Content - relative z-index to stay above link */}
            <div className="relative z-20 w-full">
                {/* Title */}
                <h3 className="font-semibold text-gray-900 text-sm mb-2 line-clamp-2 text-center h-10">
                    {market.title}
                </h3>

                {/* Outcome */}
                <p className="text-gray-700 text-sm mb-4 text-center">{market.outcome}</p>

                {/* Main Probability - Large and centered */}
                <div className="text-5xl font-bold text-blue-600 mb-6">
                    {market.probability.toFixed(1)}%
                </div>

                {/* Bottom info: Last change, side, size, time */}
                <div className="w-full text-center text-xs text-gray-600 space-y-1 pt-4 border-t border-gray-200">
                    <div className={`font-medium ${getDeltaColor(market.lastTransaction.delta)}`}>
                        Last change: {formatDelta(market.lastTransaction.delta)}
                    </div>
                    <div className="flex items-center justify-center gap-2 text-gray-500">
                        <span
                            className={`font-medium ${getSideColor(market.lastTransaction.side)}`}
                        >
                            {market.lastTransaction.side}
                        </span>
                        <span>•</span>
                        <span>Size: {market.lastTransaction.size.toFixed(2)}</span>
                        <span>•</span>
                        <span>
                            {market.lastTransaction.time ||
                                formatTime(market.lastTransaction.timestamp)}
                        </span>
                    </div>
                </div>
            </div>

            {/* Link icon indicator */}
            {market.marketUrl && (
                <div className="absolute top-2 right-2 bg-blue-500 text-white rounded-full p-2 opacity-0 group-hover:opacity-100 transition-opacity z-30 pointer-events-none">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                        />
                    </svg>
                </div>
            )}
        </div>
    );
};
