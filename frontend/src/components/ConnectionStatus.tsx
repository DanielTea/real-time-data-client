import React from "react";

interface ConnectionStatusProps {
    isConnected: boolean;
    error: string | null;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ isConnected, error }) => {
    return (
        <div className="flex items-center gap-2 mb-4">
            <div
                className={`w-3 h-3 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"}`}
            ></div>
            <span className="text-sm font-medium text-gray-700">
                {isConnected ? "Connected" : "Disconnected"}
            </span>
            {error && <span className="text-sm text-red-600 ml-2">{error}</span>}
        </div>
    );
};
