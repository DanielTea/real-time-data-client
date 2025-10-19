import { RealTimeDataClient } from "../src/client";
import { Message } from "../src/model";
import * as dotenv from "dotenv";
import * as https from "https";

// Load environment variables from keys.env
dotenv.config({ path: "./keys.env" });

console.log("[DEBUG] Script started - all-markets-probability-changes.ts");

// Store previous probabilities for delta calculation
const previousProbabilities = new Map<string, number>();
// Track active markets
const activeMarkets = new Map<string, boolean>();
// Store all markets for background checking with last seen timestamp
const allMarkets = new Map<
    string,
    { title: string; outcome: string; marketId?: string; lastSeen: number }
>();
// Track when markets were last seen in activity
const lastActivityTime = new Map<string, number>();

// Smart category detection based on keywords
function detectCategory(title: string): string | undefined {
    const titleLower = title.toLowerCase();

    // Define category keywords with priority
    const categoryKeywords: [string, string[]][] = [
        [
            "Politics",
            [
                "election",
                "political",
                "politician",
                "government",
                "senate",
                "congress",
                "parliament",
                "vote",
                "candidate",
                "campaign",
                "trump",
                "biden",
                "harris",
                "republican",
                "democrat",
            ],
        ],
        [
            "Sports",
            [
                "win",
                "nfl",
                "nba",
                "nhl",
                "nfl",
                "world cup",
                "premier league",
                "football",
                "basketball",
                "hockey",
                "soccer",
                "golf",
                "tennis",
                "champion",
                "match",
                "game",
                "team",
                "score",
                "afc",
                "psg",
                "sunderland",
                "brighton",
                "arsenal",
                "liverpool",
                "chelsea",
                "manchester",
            ],
        ],
        [
            "Crypto",
            [
                "bitcoin",
                "ethereum",
                "crypto",
                "btc",
                "eth",
                "blockchain",
                "coin",
                "token",
                "defi",
                "nft",
                "web3",
                "polygon",
                "solana",
                "cardano",
                "ripple",
                "dogecoin",
            ],
        ],
        [
            "Finance",
            [
                "stock",
                "market",
                "earnings",
                "ipo",
                "sec",
                "inflation",
                "interest rate",
                "fed",
                "treasury",
                "nasdaq",
                "dow jones",
                "s&p",
                "price",
                "bond",
                "currency",
                "dollar",
                "yuan",
                "euro",
            ],
        ],
        [
            "Tech",
            [
                "technology",
                "tech",
                "ai",
                "artificial intelligence",
                "machine learning",
                "software",
                "hardware",
                "chip",
                "semiconductor",
                "gpu",
                "cpu",
                "startup",
                "vc",
                "venture",
                "apple",
                "microsoft",
                "google",
                "amazon",
                "meta",
                "tesla",
                "openai",
            ],
        ],
        [
            "Earnings",
            [
                "earnings",
                "revenue",
                "profit",
                "quarter",
                "fy",
                "q1",
                "q2",
                "q3",
                "q4",
                "ebitda",
                "margin",
            ],
        ],
        [
            "Geopolitics",
            [
                "russia",
                "ukraine",
                "china",
                "taiwan",
                "israel",
                "iran",
                "north korea",
                "conflict",
                "war",
                "ceasefire",
                "peace",
                "treaty",
                "diplomatic",
                "international",
            ],
        ],
        [
            "Culture",
            [
                "movie",
                "film",
                "music",
                "actor",
                "actress",
                "award",
                "oscar",
                "grammy",
                "emmy",
                "entertainment",
                "celebrity",
                "show",
                "series",
                "episode",
            ],
        ],
        [
            "World",
            [
                "world",
                "global",
                "international",
                "country",
                "nation",
                "population",
                "climate",
                "environment",
                "weather",
                "natural disaster",
            ],
        ],
        [
            "Economy",
            [
                "economic",
                "gdp",
                "unemployment",
                "recession",
                "boom",
                "housing",
                "real estate",
                "commodity",
                "oil",
                "gas",
                "agriculture",
            ],
        ],
        ["Elections", ["election", "vote", "ballot", "electoral", "poll", "campaign", "candidate"]],
    ];

    // Check keywords in order of priority
    for (const [category, keywords] of categoryKeywords) {
        for (const keyword of keywords) {
            if (titleLower.includes(keyword)) {
                return category;
            }
        }
    }

    return undefined;
}

// Check individual market status by ID
async function checkMarketStatus(marketId: string): Promise<boolean> {
    return new Promise(resolve => {
        if (!marketId) {
            resolve(true); // If no ID, assume active
            return;
        }

        const options = {
            hostname: "clob.polymarket.com",
            port: 443,
            path: `/markets/${marketId}`,
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
            timeout: 5000,
        };

        const req = https.request(options, res => {
            let data = "";

            res.on("data", chunk => {
                data += chunk;
            });

            res.on("end", () => {
                try {
                    if (res.statusCode === 200) {
                        const market = JSON.parse(data);
                        // Consider market closed if:
                        // - active is false
                        // - closed is true
                        // - enable_order_book is false (means trading is disabled, likely in review)
                        const isActive =
                            market.active !== false &&
                            market.closed !== true &&
                            market.enable_order_book !== false;
                        resolve(isActive);
                    } else {
                        resolve(true); // Default to active if we can't check
                    }
                } catch (e) {
                    resolve(true);
                }
            });
        });

        req.on("error", () => {
            resolve(true); // Default to active on error
        });

        req.on("timeout", () => {
            req.destroy();
            resolve(true); // Default to active on timeout
        });

        req.end();
    });
}

// Background thread to check market status
function startMarketStatusChecker() {
    console.log("[DEBUG] Market status checker started");

    setInterval(async () => {
        if (allMarkets.size === 0) {
            return;
        }

        console.log(`[DEBUG] Checking ${allMarkets.size} markets for closure...`);

        let checked = 0;
        let deleted = 0;

        // Check each market individually (in batches to avoid overwhelming the API)
        const marketEntries = Array.from(allMarkets.entries());

        for (let i = 0; i < marketEntries.length; i++) {
            const [key, market] = marketEntries[i];

            if (!market.marketId) {
                continue; // Skip markets without ID
            }

            try {
                const isActive = await checkMarketStatus(market.marketId);
                checked++;

                if (!isActive && activeMarkets.get(key) !== false) {
                    console.log(
                        JSON.stringify({
                            title: market.title,
                            outcome: market.outcome,
                            status: "closed",
                            marketId: market.marketId,
                            action: "remove",
                        }),
                    );

                    activeMarkets.set(key, false);
                    allMarkets.delete(key);
                    deleted++;
                    console.log(`[DEBUG] Deleted market: ${key}`);
                }

                // Add small delay between checks to avoid rate limiting
                if (i < marketEntries.length - 1) {
                    await new Promise(resolve => setTimeout(resolve, 100));
                }
            } catch (e) {
                // Continue with next market on error
                console.error(`[DEBUG] Error checking market ${key}:`, e);
            }
        }

        console.log(
            `[DEBUG] Checked ${checked} markets, deleted ${deleted}. Remaining: ${allMarkets.size}`,
        );
    }, 30000); // Check every 30 seconds
}

const onMessage = (_: RealTimeDataClient, message: Message): void => {
    const payload = message.payload as any;

    // Only track activity topic for probability changes
    if (message.topic === "activity") {
        if (message.type === "trades" || message.type === "orders_matched") {
            const probability = payload.price * 100;

            // Create unique key for this market-outcome combination
            const marketKey = `${payload.title}:${payload.outcome}`;
            const marketId = payload.id || payload.market_id || payload.slug;

            // Track market for background checking
            const now = Date.now();
            const isNewMarket = !allMarkets.has(marketKey);
            allMarkets.set(marketKey, {
                title: payload.title,
                outcome: payload.outcome,
                marketId: marketId,
                lastSeen: now,
            });

            // Update last activity time
            lastActivityTime.set(marketKey, now);

            if (isNewMarket) {
                console.log(
                    `[DEBUG] Added market to tracking: ${marketKey} (total: ${allMarkets.size})`,
                );
            }

            // Check if market is active (default to true if not specified)
            const isActive = payload.active !== false;
            activeMarkets.set(marketKey, isActive);

            // Skip closed markets
            if (!isActive) {
                console.log(
                    JSON.stringify({
                        title: payload.title,
                        outcome: payload.outcome,
                        status: "closed",
                        marketId: marketId,
                        action: "remove",
                    }),
                );
                return;
            }

            // Calculate delta from previous probability
            let deltaStr = "";
            let shouldLog = false;
            let delta: number | undefined;

            if (previousProbabilities.has(marketKey)) {
                const previousProb = previousProbabilities.get(marketKey)!;
                delta = probability - previousProb;

                // Show all deltas (no threshold)
                const deltaSign = delta >= 0 ? "+" : "";
                deltaStr = ` (${deltaSign}${delta.toFixed(1)}%)`;
                shouldLog = true;
            } else {
                // Log first occurrence (no previous data)
                deltaStr = " (first occurrence)";
                shouldLog = true;
            }

            // Store current probability for next comparison
            previousProbabilities.set(marketKey, probability);

            // Log all changes
            if (shouldLog) {
                // Output as JSON so WebSocket server can parse and relay all fields
                // Try to extract category from payload or use smart detection
                let category =
                    payload.category || payload.group || detectCategory(payload.title || "");

                const logData = {
                    title: payload.title,
                    outcome: payload.outcome,
                    probability: probability,
                    delta: delta,
                    deltaStr: deltaStr.replace(" (", "").replace(")", ""),
                    side: payload.side,
                    size: payload.size,
                    marketId: marketId,
                    category: category,
                    active: true,
                    timestamp: Date.now(),
                    // Market URL: https://polymarket.com/market/{marketId}
                    marketUrl: marketId ? `https://polymarket.com/market/${marketId}` : undefined,
                };
                console.log(JSON.stringify(logData));
            }
        }
    }
};

const onConnect = (client: RealTimeDataClient): void => {
    console.log("Connected to Polymarket WebSocket - All Market Probability Changes");

    // Subscribe to activity feed for probability changes
    client.subscribe({
        subscriptions: [
            {
                topic: "activity",
                type: "*",
            },
        ],
    });

    // Start background market status checker
    startMarketStatusChecker();
};

new RealTimeDataClient({ onConnect, onMessage }).connect();
