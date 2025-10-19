// IndexedDB for caching market data
const DB_NAME = "PolymarketCache";
const STORE_NAME = "markets";
const DB_VERSION = 1;

interface CachedMarket {
    key: string; // title:outcome
    title: string;
    outcome: string;
    probability: number;
    delta?: number;
    side: "BUY" | "SELL";
    size: number;
    timestamp: number;
    marketUrl?: string;
    lastUpdated: number;
}

interface CachedPage {
    pageNumber: number;
    markets: CachedMarket[];
}

let db: IDBDatabase | null = null;

export const initDb = async (): Promise<IDBDatabase> => {
    if (db) return db;

    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onerror = () => {
            console.error("Failed to open IndexedDB:", request.error);
            reject(request.error);
        };

        request.onsuccess = () => {
            db = request.result;
            resolve(db);
        };

        request.onupgradeneeded = event => {
            const database = (event.target as IDBOpenDBRequest).result;
            console.log("Creating IndexedDB object store:", STORE_NAME);
            if (!database.objectStoreNames.contains(STORE_NAME)) {
                database.createObjectStore(STORE_NAME, { keyPath: "key" });
            }
        };
    });
};

export const saveMarkets = async (pages: CachedPage[]): Promise<void> => {
    if (!db) await initDb();

    return new Promise((resolve, reject) => {
        const transaction = db!.transaction([STORE_NAME], "readwrite");
        const store = transaction.objectStore(STORE_NAME);

        // Clear old data
        store.clear();

        // Count and save all markets from all pages
        let totalMarkets = 0;
        pages.forEach(page => {
            page.markets.forEach(market => {
                // Create key field if it doesn't exist
                const marketToSave = {
                    ...market,
                    key: `${market.title}:${market.outcome}`,
                    lastUpdated: Date.now(),
                };
                store.add(marketToSave);
                totalMarkets++;
            });
        });

        transaction.oncomplete = () => {
            resolve();
        };
        transaction.onerror = () => {
            console.error("Failed to save markets to cache:", transaction.error);
            reject(transaction.error);
        };
    });
};

export const loadMarkets = async (): Promise<CachedPage[]> => {
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
            const markets: CachedMarket[] = request.result;

            if (markets.length === 0) {
                resolve([]);
                return;
            }

            // Group markets into pages (50 per page)
            const pages: CachedPage[] = [];
            const MARKETS_PER_PAGE = 50;

            for (let i = 0; i < markets.length; i += MARKETS_PER_PAGE) {
                const pageNumber = Math.floor(i / MARKETS_PER_PAGE);
                pages.push({
                    pageNumber,
                    markets: markets.slice(i, i + MARKETS_PER_PAGE),
                });
            }

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
    return new Promise((resolve, reject) => {
        // Close existing connection
        if (db) {
            db.close();
            db = null;
        }

        // Delete the entire database
        const deleteRequest = indexedDB.deleteDatabase(DB_NAME);

        deleteRequest.onerror = () => {
            console.error("Failed to delete database:", deleteRequest.error);
            reject(deleteRequest.error);
        };

        deleteRequest.onsuccess = () => {
            console.log("Database deleted successfully");
            resolve();
        };
    });
};
