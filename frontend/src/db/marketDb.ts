import type { MarketData, LastTransaction } from "../types";

// IndexedDB for caching market data
const DB_NAME = "PolymarketCache";
const STORE_NAME = "markets";
const DB_VERSION = 3; // Incremented to support lastTransaction structure

interface CachedMarket {
    key: string; // title:outcome
    title: string;
    outcome: string;
    probability: number;
    marketId?: string;
    category?: string;
    active?: boolean;
    marketUrl?: string;
    description?: string;
    lastTransaction: LastTransaction;
    lastUpdated: number;
}

let db: IDBDatabase | null = null;

export const initDb = async (): Promise<IDBDatabase> => {
    if (db && db.version === DB_VERSION) {
        console.log("[IndexedDB] Using existing database connection");
        return db;
    }

    // Close existing connection if version mismatch
    if (db) {
        console.log("[IndexedDB] Closing old database connection");
        db.close();
        db = null;
    }

    console.log(`[IndexedDB] Opening database ${DB_NAME} version ${DB_VERSION}`);

    return new Promise((resolve, reject) => {
        // Set timeout to detect hangs
        const timeout = setTimeout(() => {
            console.error("[IndexedDB] Database open timeout - deleting and retrying");
            reject(new Error("Database open timeout"));
        }, 5000);

        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onerror = () => {
            clearTimeout(timeout);
            console.error("[IndexedDB] Failed to open database:", request.error);
            reject(request.error);
        };

        request.onsuccess = () => {
            clearTimeout(timeout);
            db = request.result;
            console.log(`[IndexedDB] Database opened successfully (version ${db.version})`);
            resolve(db);
        };

        request.onupgradeneeded = event => {
            console.log(
                `[IndexedDB] Upgrading database from version ${event.oldVersion} to ${DB_VERSION}`,
            );
            const database = (event.target as IDBOpenDBRequest).result;

            // Delete old store if it exists
            if (database.objectStoreNames.contains(STORE_NAME)) {
                console.log(`[IndexedDB] Deleting old object store: ${STORE_NAME}`);
                database.deleteObjectStore(STORE_NAME);
            }

            console.log(`[IndexedDB] Creating new object store: ${STORE_NAME}`);
            database.createObjectStore(STORE_NAME, { keyPath: "key" });
            console.log("[IndexedDB] Object store created successfully");
        };

        request.onblocked = () => {
            clearTimeout(timeout);
            console.warn(
                "[IndexedDB] Database upgrade blocked - close all other tabs using this site",
            );
            reject(new Error("Database upgrade blocked"));
        };
    });
};

export const saveMarkets = async (
    pages: { pageNumber: number; markets: MarketData[] }[],
): Promise<void> => {
    if (!db) await initDb();

    return new Promise((resolve, reject) => {
        const transaction = db!.transaction([STORE_NAME], "readwrite");
        const store = transaction.objectStore(STORE_NAME);

        // Clear old data
        store.clear();

        // Count and save all markets from all pages
        let totalMarkets = 0;
        let failedMarkets = 0;
        pages.forEach(page => {
            page.markets.forEach(market => {
                try {
                    // Convert MarketData to CachedMarket
                    const marketToSave: CachedMarket = {
                        key: `${market.title}:${market.outcome}`,
                        title: market.title,
                        outcome: market.outcome,
                        probability: market.probability,
                        marketId: market.marketId,
                        category: market.category,
                        active: market.active,
                        marketUrl: market.marketUrl,
                        description: market.description,
                        lastTransaction: market.lastTransaction,
                        lastUpdated: Date.now(),
                    };
                    store.add(marketToSave);
                    totalMarkets++;
                } catch (err) {
                    console.error(
                        `[IndexedDB] Failed to add market ${market.title}:${market.outcome}`,
                        err,
                    );
                    failedMarkets++;
                }
            });
        });

        if (failedMarkets > 0) {
            console.warn(`[IndexedDB] Failed to add ${failedMarkets} markets`);
        }

        transaction.oncomplete = () => {
            console.log(`[IndexedDB] Saved ${totalMarkets} markets to cache`);
            resolve();
        };
        transaction.onerror = event => {
            console.error("Failed to save markets to cache:", transaction.error);
            console.error("Transaction error event:", event);
            reject(transaction.error);
        };

        transaction.onabort = event => {
            console.error("Transaction aborted:", event);
            reject(new Error("Transaction aborted"));
        };
    });
};

export const loadMarkets = async (): Promise<{ pageNumber: number; markets: MarketData[] }[]> => {
    if (!db) await initDb();

    return new Promise((resolve, reject) => {
        const transaction = db!.transaction([STORE_NAME], "readonly");
        const store = transaction.objectStore(STORE_NAME);
        const request = store.getAll();

        request.onerror = () => {
            console.error("Failed to load markets from cache:", request.error);
            reject(request.error);
        };

        request.onsuccess = () => {
            const cachedMarkets: CachedMarket[] = request.result;

            console.log(`[IndexedDB] Loaded ${cachedMarkets.length} markets from cache`);

            if (cachedMarkets.length === 0) {
                resolve([]);
                return;
            }

            // Convert CachedMarket to MarketData
            const markets: MarketData[] = cachedMarkets.map(cached => ({
                title: cached.title,
                outcome: cached.outcome,
                probability: cached.probability,
                marketId: cached.marketId,
                category: cached.category,
                active: cached.active,
                marketUrl: cached.marketUrl,
                description: cached.description,
                lastTransaction: cached.lastTransaction,
            }));

            // Group markets into pages (50 per page)
            const pages: { pageNumber: number; markets: MarketData[] }[] = [];
            const MARKETS_PER_PAGE = 50;

            for (let i = 0; i < markets.length; i += MARKETS_PER_PAGE) {
                const pageNumber = Math.floor(i / MARKETS_PER_PAGE);
                pages.push({
                    pageNumber,
                    markets: markets.slice(i, i + MARKETS_PER_PAGE),
                });
            }

            console.log(`[IndexedDB] Organized into ${pages.length} pages`);
            resolve(pages);
        };
    });
};

export const clearCache = async (): Promise<void> => {
    if (!db) await initDb();

    return new Promise((resolve, reject) => {
        const transaction = db!.transaction([STORE_NAME], "readwrite");
        const store = transaction.objectStore(STORE_NAME);
        store.clear();

        transaction.oncomplete = () => {
            console.log("Cache cleared successfully");
            // Reset the db reference so it will be re-initialized on next load
            if (db) db.close();
            db = null;
            resolve();
        };
        transaction.onerror = () => {
            console.error("Failed to clear cache:", transaction.error);
            reject(transaction.error);
        };
    });
};

export const deleteDatabase = (): Promise<void> => {
    console.log("[IndexedDB] Deleting database...");
    return new Promise((resolve, reject) => {
        // Close existing connection
        if (db) {
            console.log("[IndexedDB] Closing database connection before delete");
            db.close();
            db = null;
        }

        // Delete the entire database
        console.log(`[IndexedDB] Requesting deletion of ${DB_NAME}`);
        const deleteRequest = indexedDB.deleteDatabase(DB_NAME);

        deleteRequest.onerror = () => {
            console.error("[IndexedDB] Failed to delete database:", deleteRequest.error);
            reject(deleteRequest.error);
        };

        deleteRequest.onsuccess = () => {
            console.log(`[IndexedDB] Database ${DB_NAME} deleted successfully`);
            resolve();
        };

        deleteRequest.onblocked = () => {
            console.warn("[IndexedDB] Database deletion blocked - close all tabs using this site");
            reject(new Error("Database deletion blocked"));
        };
    });
};
