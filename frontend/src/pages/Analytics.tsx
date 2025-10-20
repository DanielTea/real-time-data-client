import React from "react";
import { useWebSocket } from "../hooks/useWebSocket";

export const Analytics: React.FC = () => {
    const { pages } = useWebSocket("ws://localhost:8080");
    const allMarkets = pages.flatMap(page => page.markets);

    // Calculate analytics
    const totalMarkets = allMarkets.length;
    const avgProbability =
        allMarkets.length > 0
            ? (allMarkets.reduce((sum, m) => sum + m.probability, 0) / allMarkets.length).toFixed(2)
            : "0.00";

    const positiveDeltas = allMarkets.filter(m => (m.lastTransaction.delta || 0) > 0).length;
    const negativeDeltas = allMarkets.filter(m => (m.lastTransaction.delta || 0) < 0).length;

    // Category breakdown
    const categoryBreakdown = allMarkets.reduce(
        (acc, market) => {
            const category = market.category || "Uncategorized";
            acc[category] = (acc[category] || 0) + 1;
            return acc;
        },
        {} as Record<string, number>,
    );

    const allCategories = Object.entries(categoryBreakdown).sort(([, a], [, b]) => b - a);

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Analytics Dashboard</h1>
                <p className="text-gray-600">Statistical insights from Polymarket real-time data</p>
            </div>

            {/* Stats Grid */}
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <div className="text-sm font-medium text-gray-500 mb-1">Total Markets</div>
                    <div className="text-3xl font-bold text-gray-900">{totalMarkets}</div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <div className="text-sm font-medium text-gray-500 mb-1">Avg Probability</div>
                    <div className="text-3xl font-bold text-gray-900">{avgProbability}%</div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <div className="text-sm font-medium text-gray-500 mb-1">Positive Changes</div>
                    <div className="text-3xl font-bold text-green-600">{positiveDeltas}</div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <div className="text-sm font-medium text-gray-500 mb-1">Negative Changes</div>
                    <div className="text-3xl font-bold text-red-600">{negativeDeltas}</div>
                </div>
            </div>

            {/* All Categories */}
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h2 className="text-xl font-bold text-gray-900 mb-4">
                    All Categories ({allCategories.length})
                </h2>
                <div className="space-y-4 max-h-[600px] overflow-y-auto">
                    {allCategories.map(([category, count]) => (
                        <div key={category} className="flex items-center justify-between">
                            <div className="flex-1">
                                <div className="text-sm font-medium text-gray-900">{category}</div>
                                <div className="mt-1 bg-gray-200 rounded-full h-2 overflow-hidden">
                                    <div
                                        className="bg-blue-600 h-full"
                                        style={{ width: `${(count / totalMarkets) * 100}%` }}
                                    />
                                </div>
                            </div>
                            <div className="ml-4 text-sm font-semibold text-gray-700">
                                {count} ({((count / totalMarkets) * 100).toFixed(1)}%)
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
