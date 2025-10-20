import React from "react";

export const About: React.FC = () => {
    return (
        <div className="container mx-auto px-4 py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">About</h1>
                <p className="text-gray-600">Polymarket Real-Time Data Client</p>
            </div>

            <div className="max-w-3xl space-y-6">
                {/* Project Info */}
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Project Overview</h2>
                    <p className="text-gray-700 mb-3">
                        A real-time WebSocket client for monitoring Polymarket probability changes
                        with a React frontend dashboard.
                    </p>
                    <p className="text-gray-700">
                        This application provides live updates on probability changes across all
                        Polymarket markets, with advanced filtering, search capabilities, and
                        real-time analytics.
                    </p>
                </div>

                {/* Features */}
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Key Features</h2>
                    <ul className="space-y-2 text-gray-700">
                        <li className="flex items-start gap-2">
                            <span className="text-green-600 font-bold">✓</span>
                            <span>Real-time probability monitoring across all markets</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <span className="text-green-600 font-bold">✓</span>
                            <span>Delta visualization with color-coded indicators</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <span className="text-green-600 font-bold">✓</span>
                            <span>Category filtering and keyword search</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <span className="text-green-600 font-bold">✓</span>
                            <span>IndexedDB-based market data caching</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <span className="text-green-600 font-bold">✓</span>
                            <span>WebSocket streaming for live updates</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <span className="text-green-600 font-bold">✓</span>
                            <span>Analytics dashboard with market insights</span>
                        </li>
                    </ul>
                </div>

                {/* Tech Stack */}
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Technology Stack</h2>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <div className="font-semibold text-gray-900 mb-1">Frontend</div>
                            <ul className="space-y-1 text-gray-600">
                                <li>• React 19</li>
                                <li>• TypeScript</li>
                                <li>• Tailwind CSS</li>
                                <li>• React Router</li>
                                <li>• Vite</li>
                            </ul>
                        </div>
                        <div>
                            <div className="font-semibold text-gray-900 mb-1">Backend</div>
                            <ul className="space-y-1 text-gray-600">
                                <li>• Node.js</li>
                                <li>• WebSocket (ws)</li>
                                <li>• Polymarket API</li>
                                <li>• IndexedDB</li>
                            </ul>
                        </div>
                    </div>
                </div>

                {/* Version Info */}
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">
                        Version Information
                    </h2>
                    <div className="text-sm text-gray-700 space-y-1">
                        <div>
                            <span className="font-semibold">Version:</span> 1.0.0
                        </div>
                        <div>
                            <span className="font-semibold">License:</span> MIT
                        </div>
                        <div>
                            <span className="font-semibold">Repository:</span>{" "}
                            <a href="https://github.com" className="text-blue-600 hover:underline">
                                GitHub
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
