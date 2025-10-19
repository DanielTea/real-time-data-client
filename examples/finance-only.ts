import { RealTimeDataClient } from "../src/client";
import { Message } from "../src/model";
import * as dotenv from "dotenv";

// Load environment variables from keys.env
dotenv.config({ path: "./keys.env" });

const onMessage = (_: RealTimeDataClient, message: Message): void => {
    const payload = message.payload as any;

    // Focus on real-time market data and price changes for ALL markets
    if (message.topic === "crypto_prices" || message.topic === "crypto_prices_chainlink") {
        console.log(
            `[CRYPTO PRICE] ${payload.symbol}: $${payload.value} (${new Date(payload.timestamp).toLocaleTimeString()})`,
        );
    } else if (message.topic === "clob_market") {
        if (message.type === "price_change") {
            console.log(
                `[PRICE CHANGE] Market ${payload.m}: ${JSON.stringify(payload.pc)} (${new Date(payload.t).toLocaleTimeString()})`,
            );
        } else if (message.type === "last_trade_price") {
            console.log(
                `[LAST TRADE] Market ${payload.market}: $${payload.price} (${payload.side}) Size: ${payload.size}`,
            );
        } else if (message.type === "agg_orderbook") {
            console.log(
                `[ORDERBOOK] Market ${payload.market}: Best Bid: $${payload.bids[0]?.price} (${payload.bids[0]?.size}) | Best Ask: $${payload.asks[0]?.price} (${payload.asks[0]?.size})`,
            );
        }
    } else if (message.topic === "clob_user") {
        if (message.type === "order") {
            console.log(
                `[USER ORDER] ${payload.type}: ${payload.side} ${payload.outcome} @ $${payload.price} (${payload.status})`,
            );
        } else if (message.type === "trade") {
            console.log(
                `[USER TRADE] ${payload.side} ${payload.outcome} @ $${payload.price} Size: ${payload.size}`,
            );
        }
    } else if (message.topic === "activity") {
        // Show probability changes from trades and orders
        if (message.type === "trades" || message.type === "orders_matched") {
            console.log(
                `[PROBABILITY CHANGE] ${payload.title}: ${payload.outcome} @ $${payload.price} (${payload.side}) Size: ${payload.size}`,
            );
        }
    }
};

const onConnect = (client: RealTimeDataClient): void => {
    console.log("Connected to Polymarket WebSocket - All Market Probability Changes");

    // Subscribe to ALL market data feeds to track probability changes
    client.subscribe({
        subscriptions: [
            // Activity - trades and orders that change probabilities
            {
                topic: "activity",
                type: "*",
                // No filters to get all markets
            },

            // Crypto prices - real-time price updates
            {
                topic: "crypto_prices",
                type: "*",
                filters: `{"symbol":"btcusdt"}`,
            },

            // Chainlink crypto prices
            {
                topic: "crypto_prices_chainlink",
                type: "*",
                filters: `{"symbol":"btc/usd"}`,
            },

            // CLOB market data - price changes, orderbook, last trade prices
            {
                topic: "clob_market",
                type: "*",
                filters: `["71321045679252212594626385532706912750332728571942532289631379312455583992563"]`,
            },

            // CLOB user data - your orders and trades
            {
                topic: "clob_user",
                type: "*",
                clob_auth: {
                    key: process.env.CLOB_API_KEY!,
                    secret: process.env.CLOB_SECRET!,
                    passphrase: process.env.CLOB_PASSPHRASE!,
                },
            },
        ],
    });
};

new RealTimeDataClient({ onConnect, onMessage }).connect();
