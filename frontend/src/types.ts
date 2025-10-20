export interface LastTransaction {
    delta?: number;
    deltaStr?: string;
    side: "BUY" | "SELL";
    size: number;
    timestamp: number;
    time?: string;
}

export interface MarketData {
    title: string;
    outcome: string;
    probability: number;
    marketId?: string;
    category?: string;
    active?: boolean;
    marketUrl?: string;
    description?: string;
    lastTransaction: LastTransaction;
}

export interface WebSocketMessage {
    topic: string;
    type: string;
    timestamp: number;
    connection_id: string;
    payload: any;
}
