export interface MarketData {
    title: string;
    outcome: string;
    probability: number;
    delta?: number;
    side: "BUY" | "SELL";
    size: number;
    timestamp: number;
    icon?: string;
    marketUrl?: string;
    category?: string;
    active?: boolean;
}

export interface WebSocketMessage {
    topic: string;
    type: string;
    timestamp: number;
    connection_id: string;
    payload: any;
}
