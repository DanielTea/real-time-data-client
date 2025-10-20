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
// Store market descriptions and metadata
const marketDescriptions = new Map<string, string>();
const marketCategories = new Map<string, string>();

// Fetch market metadata (description and category via tags) by market ID
async function fetchMarketMetadata(
    marketId: string,
): Promise<{ description?: string; category?: string }> {
    return new Promise(async resolve => {
        if (!marketId) {
            resolve({});
            return;
        }

        try {
            // First, get market by slug to get the numeric ID and description
            const marketData = await new Promise<any>(res => {
                const options = {
                    hostname: "gamma-api.polymarket.com",
                    port: 443,
                    path: `/markets?slug=${marketId}&limit=1`,
                    method: "GET",
                    headers: { "Content-Type": "application/json" },
                    timeout: 5000,
                };

                const req = https.request(options, response => {
                    let data = "";
                    response.on("data", chunk => {
                        data += chunk;
                    });
                    response.on("end", () => {
                        try {
                            const markets = JSON.parse(data);
                            if (Array.isArray(markets) && markets.length > 0) {
                                res(markets[0]);
                            } else {
                                res(null);
                            }
                        } catch (e) {
                            res(null);
                        }
                    });
                });
                req.on("error", () => res(null));
                req.on("timeout", () => {
                    req.destroy();
                    res(null);
                });
                req.end();
            });

            if (!marketData || !marketData.id) {
                resolve({});
                return;
            }

            // Now fetch tags using the numeric market ID
            const tagsData = await new Promise<any[]>(res => {
                const options = {
                    hostname: "gamma-api.polymarket.com",
                    port: 443,
                    path: `/markets/${marketData.id}/tags`,
                    method: "GET",
                    headers: { "Content-Type": "application/json" },
                    timeout: 5000,
                };

                const req = https.request(options, response => {
                    let data = "";
                    response.on("data", chunk => {
                        data += chunk;
                    });
                    response.on("end", () => {
                        try {
                            const tags = JSON.parse(data);
                            res(Array.isArray(tags) ? tags : []);
                        } catch (e) {
                            res([]);
                        }
                    });
                });
                req.on("error", () => res([]));
                req.on("timeout", () => {
                    req.destroy();
                    res([]);
                });
                req.end();
            });

            // Use the first tag as the category (tags are ordered by relevance)
            const category = tagsData.length > 0 ? tagsData[0].label : undefined;

            resolve({
                description: marketData.description || undefined,
                category: category,
            });
        } catch (e) {
            resolve({});
        }
    });
}

// Check individual market status by slug
async function checkMarketStatus(marketSlug: string): Promise<boolean> {
    return new Promise(resolve => {
        if (!marketSlug) {
            resolve(true); // If no slug, assume active
            return;
        }

        const options = {
            hostname: "gamma-api.polymarket.com",
            port: 443,
            path: `/markets?slug=${marketSlug}&limit=1`,
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

            res.on("end", async () => {
                try {
                    if (res.statusCode === 200) {
                        const markets = JSON.parse(data);
                        if (Array.isArray(markets) && markets.length > 0) {
                            const market = markets[0];

                            // Store description if available
                            if (market.description) {
                                marketDescriptions.set(marketSlug, market.description);
                            }

                            // Fetch tags for category if we have numeric ID
                            if (market.id && !marketCategories.has(marketSlug)) {
                                const tagsOptions = {
                                    hostname: "gamma-api.polymarket.com",
                                    port: 443,
                                    path: `/markets/${market.id}/tags`,
                                    method: "GET",
                                    headers: { "Content-Type": "application/json" },
                                    timeout: 3000,
                                };

                                https
                                    .get(tagsOptions, tagsRes => {
                                        let tagsData = "";
                                        tagsRes.on("data", chunk => {
                                            tagsData += chunk;
                                        });
                                        tagsRes.on("end", () => {
                                            try {
                                                const tags = JSON.parse(tagsData);
                                                if (Array.isArray(tags) && tags.length > 0) {
                                                    marketCategories.set(marketSlug, tags[0].label);
                                                }
                                            } catch (e) {
                                                /* ignore */
                                            }
                                        });
                                    })
                                    .on("error", () => {
                                        /* ignore */
                                    });
                            }

                            // Consider market closed if active is false or closed is true
                            const isActive = market.active !== false && market.closed !== true;
                            resolve(isActive);
                        } else {
                            resolve(true); // Market not found, assume active
                        }
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

            // Fetch metadata for markets that don't have it yet (new or missing)
            if (marketId && !marketDescriptions.has(marketId)) {
                // Fire and forget - will be picked up on next update
                fetchMarketMetadata(marketId)
                    .then(metadata => {
                        if (metadata.description) {
                            marketDescriptions.set(marketId, metadata.description);
                        }
                        if (metadata.category) {
                            marketCategories.set(marketId, metadata.category);
                            // Re-emit market with correct category
                            console.log(
                                JSON.stringify({
                                    title: payload.title,
                                    outcome: payload.outcome,
                                    probability: probability,
                                    marketId: marketId,
                                    category: metadata.category,
                                    active: true,
                                    marketUrl: marketId
                                        ? `https://polymarket.com/market/${marketId}`
                                        : undefined,
                                    description: metadata.description,
                                    lastTransaction: {
                                        delta: undefined,
                                        deltaStr: "category update",
                                        side: payload.side,
                                        size: payload.size,
                                        timestamp: Date.now(),
                                        time: new Date().toLocaleString("en-US", {
                                            year: "numeric",
                                            month: "2-digit",
                                            day: "2-digit",
                                            hour: "2-digit",
                                            minute: "2-digit",
                                            second: "2-digit",
                                            hour12: false,
                                        }),
                                    },
                                    action: "update_metadata",
                                }),
                            );
                        }
                    })
                    .catch(() => {
                        // Ignore errors
                    });
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
                // ONLY use API or payload category - no keyword fallback
                let category =
                    (marketId ? marketCategories.get(marketId) : undefined) ||
                    payload.category ||
                    payload.group ||
                    undefined; // Will be "Uncategorized" until API fetch completes

                const timestamp = Date.now();
                const date = new Date(timestamp);
                const humanReadableTime = date.toLocaleString("en-US", {
                    year: "numeric",
                    month: "2-digit",
                    day: "2-digit",
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                    hour12: false,
                });

                const logData = {
                    title: payload.title,
                    outcome: payload.outcome,
                    probability: probability,
                    marketId: marketId,
                    category: category,
                    active: true,
                    // Market URL: https://polymarket.com/market/{marketId}
                    marketUrl: marketId ? `https://polymarket.com/market/${marketId}` : undefined,
                    // Include description if available
                    description: marketId ? marketDescriptions.get(marketId) : undefined,
                    // Last transaction details (changes frequently)
                    lastTransaction: {
                        delta: delta,
                        deltaStr: deltaStr.replace(" (", "").replace(")", ""),
                        side: payload.side,
                        size: payload.size,
                        timestamp: timestamp,
                        time: humanReadableTime,
                    },
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
