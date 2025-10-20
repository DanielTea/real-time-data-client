import React, { useState } from "react";

export const Settings: React.FC = () => {
    const [wsUrl, setWsUrl] = useState("ws://localhost:8080");

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Settings</h1>
                <p className="text-gray-600">Configure your Polymarket dashboard preferences</p>
            </div>

            <div className="max-w-2xl space-y-6">
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
