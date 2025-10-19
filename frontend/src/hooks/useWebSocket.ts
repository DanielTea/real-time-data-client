import { useEffect, useRef, useState } from "react";
import type { MarketData, WebSocketMessage } from "../types";
import { initDb, loadMarkets, saveMarkets } from "../db/marketDb";

export interface MarketPage {
    pageNumber: number;
    markets: MarketData[];
}

export const useWebSocket = (url: string) => {
    const [isConnected, setIsConnected] = useState(false);
    const [pages, setPages] = useState<MarketPage[]>([]);
    const [error, setError] = useState<string | null>(null);
    const ws = useRef<WebSocket | null>(null);
    const previousProbabilities = useRef<Map<string, number>>(new Map());
    const MARKETS_PER_PAGE = 50;

    // Load cached markets on mount
    useEffect(() => {
        const loadCachedData = async () => {
            try {
                await initDb();
                const cachedPages = await loadMarkets();
                if (cachedPages.length > 0) {
                    setPages(cachedPages);

                    // Restore previous probabilities from cache
                    cachedPages.forEach(page => {
                        page.markets.forEach(market => {
                            const key = `${market.title}:${market.outcome}`;
                            previousProbabilities.current.set(key, market.probability);
                        });
                    });
                }
            } catch (err) {
                console.error("Failed to load cache:", err);
            }
        };

        loadCachedData();
    }, []);

    // Save markets to cache with debouncing
    useEffect(() => {
        // Save immediately on first market arrival
        if (pages.length > 0 && pages.some(p => p.markets.length > 0)) {
            saveMarkets(pages).catch(err => console.error("Failed to save cache:", err));
        }

        // Then set up a debounced save for subsequent updates
        const saveTimeout = setTimeout(() => {
            if (pages.length > 0) {
                saveMarkets(pages).catch(err => console.error("Failed to save cache:", err));
            }
        }, 5000); // Save every 5 seconds after changes

        return () => clearTimeout(saveTimeout);
    }, [pages]);

    useEffect(() => {
        const handleMessage = (data: any) => {
            // Handle market removal (closed markets)
            if (data.action === "remove") {
                console.log("Removing closed market:", data.title);
                setPages(prev => {
                    const updated = prev
                        .map(page => ({
                            ...page,
                            markets: page.markets.filter(
                                m => !(m.title === data.title && m.outcome === data.outcome),
                            ),
                        }))
                        .filter(page => page.markets.length > 0); // Remove empty pages
                    return updated;
                });
                return;
            }

            // Handle market data objects directly from the WebSocket server
            if (data.title && data.outcome && data.probability !== undefined) {
                const marketKey = `${data.title}:${data.outcome}`;

                // Calculate delta if not already provided
                let delta: number | undefined = data.delta;
                if (delta === undefined && previousProbabilities.current.has(marketKey)) {
                    const previousProb = previousProbabilities.current.get(marketKey)!;
                    delta = data.probability - previousProb;
                }

                // Store current probability
                previousProbabilities.current.set(marketKey, data.probability);

                // Show all changes (removed >= 10% threshold)
                const marketData: MarketData = {
                    title: data.title,
                    outcome: data.outcome,
                    probability: data.probability,
                    delta,
                    side: data.side,
                    size: data.size,
                    timestamp: data.timestamp,
                    icon: data.icon,
                    marketUrl: data.marketUrl,
                    category: data.category,
                    active: data.active !== false,
                };

                setPages(prev => {
                    // Search all pages for existing market
                    let foundPageIndex = -1;
                    let foundMarketIndex = -1;

                    for (let i = 0; i < prev.length; i++) {
                        const marketIndex = prev[i].markets.findIndex(
                            m => m.title === data.title && m.outcome === data.outcome,
                        );
                        if (marketIndex >= 0) {
                            foundPageIndex = i;
                            foundMarketIndex = marketIndex;
                            break;
                        }
                    }

                    // If market exists, update it in place
                    if (foundPageIndex >= 0) {
                        const updated = [...prev];
                        updated[foundPageIndex] = {
                            ...updated[foundPageIndex],
                            markets: updated[foundPageIndex].markets.map((m, idx) =>
                                idx === foundMarketIndex ? marketData : m,
                            ),
                        };
                        return updated;
                    }

                    // If market doesn't exist, add it to the last page if it has room
                    if (prev.length === 0) {
                        // Create first page
                        return [{ pageNumber: 0, markets: [marketData] }];
                    }

                    const lastPage = prev[prev.length - 1];
                    if (lastPage.markets.length < MARKETS_PER_PAGE) {
                        // Add to last page
                        const updated = [...prev];
                        updated[prev.length - 1] = {
                            ...lastPage,
                            markets: [...lastPage.markets, marketData],
                        };
                        return updated;
                    } else {
                        // Create new page
                        const newPageNumber = lastPage.pageNumber + 1;
                        return [...prev, { pageNumber: newPageNumber, markets: [marketData] }];
                    }
                });
            }
        };

        const connect = () => {
            try {
                ws.current = new WebSocket(url);

                ws.current.onopen = () => {
                    setIsConnected(true);
                    setError(null);
                    console.log("Connected to WebSocket");
                };

                ws.current.onmessage = event => {
                    try {
                        const data = JSON.parse(event.data);
                        handleMessage(data);
                    } catch (err) {
                        console.error("Error parsing message:", err);
                    }
                };

                ws.current.onclose = () => {
                    setIsConnected(false);
                    console.log("WebSocket disconnected");
                    // Attempt to reconnect after 3 seconds
                    setTimeout(connect, 3000);
                };

                ws.current.onerror = error => {
                    setError("WebSocket connection error");
                    console.error("WebSocket error:", error);
                };
            } catch (err) {
                setError("Failed to create WebSocket connection");
                console.error("Connection error:", err);
            }
        };

        connect();

        return () => {
            if (ws.current) {
                ws.current.close();
            }
        };
    }, [url]);

    return { isConnected, pages, error };
};
