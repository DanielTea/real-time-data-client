const WebSocket = require("ws");
const { spawn } = require("child_process");

// Create WebSocket server
const wss = new WebSocket.Server({ port: 8080 });

console.log("WebSocket server running on ws://localhost:8080");

// Store connected clients
const clients = new Set();

wss.on("connection", ws => {
    console.log("Client connected");
    clients.add(ws);

    ws.on("close", () => {
        console.log("Client disconnected");
        clients.delete(ws);
    });

    ws.on("error", error => {
        console.error("WebSocket error:", error);
        clients.delete(ws);
    });
});

// Start the TypeScript client and pipe its output
const clientProcess = spawn(
    "pnpm",
    ["exec", "ts-node", "examples/all-markets-probability-changes.ts"],
    {
        cwd: __dirname,
        stdio: ["pipe", "pipe", "pipe"],
    },
);

let buffer = "";

clientProcess.stdout.on("data", data => {
    buffer += data.toString();

    // Process complete lines
    const lines = buffer.split("\n");
    buffer = lines.pop() || ""; // Keep incomplete line in buffer

    lines.forEach(line => {
        if (line.trim()) {
            try {
                // Parse as JSON from TypeScript client
                const parsed = JSON.parse(line);
                broadcast(parsed);
            } catch (e) {
                // Print non-JSON lines (debug logs, connection messages, etc.)
                console.log(line);
            }
        }
    });
});

clientProcess.stderr.on("data", data => {
    console.error("Client error:", data.toString());
});

clientProcess.on("close", code => {
    console.log(`Client process exited with code ${code}`);
    // Restart the client process after 5 seconds
    setTimeout(() => {
        console.log("Restarting client process...");
        // This would restart the process, but for now just log
    }, 5000);
});

function broadcast(data) {
    const message = JSON.stringify(data);
    clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(message);
        }
    });
}

// Graceful shutdown
process.on("SIGINT", () => {
    console.log("Shutting down...");
    clientProcess.kill();
    wss.close();
    process.exit(0);
});
