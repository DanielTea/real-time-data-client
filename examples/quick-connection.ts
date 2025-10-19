import { RealTimeDataClient } from "../src/client";
import { Message } from "../src/model";
import * as dotenv from "dotenv";

// Load environment variables from keys.env
dotenv.config({ path: "./keys.env" });

const onMessage = (_: RealTimeDataClient, message: Message): void => {
    console.log(
        message.topic,
        message.type,
        message.timestamp,
        message.connection_id,
        message.payload,
    );
};

const onConnect = (client: RealTimeDataClient): void => {
    // Subscribe to finance-related topics only
    client.subscribe({
        subscriptions: [
            // Finance-related activity (trades, orders) - filter for finance events
            {
                topic: "activity",
                type: "*",
                filters: `{"event_slug":"fed-rate-cut"}`,
            },

            // Crypto prices for financial markets
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

            // CLOB market data for finance markets
            {
                topic: "clob_market",
                type: "*",
                filters: `["71321045679252212594626385532706912750332728571942532289631379312455583992563"]`,
            },

            // CLOB user data for authenticated finance trading
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

    /*
    // Unsubscribe from a topic
    client.subscribe({
        subscriptions: [
            {
                topic: "activity",
                type: "trades",
            },
        ],
    });
    */
};

new RealTimeDataClient({ onConnect, onMessage }).connect();
