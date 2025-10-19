# Polymarket Real-Time Data Client

A real-time WebSocket client for monitoring Polymarket probability changes with a React frontend dashboard.

## Features

- **Real-time probability monitoring**: Track all probability changes across Polymarket markets
- **Delta visualization**: See probability changes with color-coded indicators (green/red)
- **Category filtering**: Filter markets by Polymarket categories (Politics, Sports, Crypto, Finance, Tech, etc.)
- **Keyword search**: Search markets by title or outcome
- **Automatic market cleanup**: Closed markets are automatically removed from the UI
- **Modern UI**: Clean, responsive React interface with Tailwind CSS
- **WebSocket streaming**: Live updates without page refresh
- **Local caching**: IndexedDB-based market data cache - no need to re-stream markets on reload
- **Clickable markets**: Click any card to open the market on Polymarket in a new tab
- **Market persistence**: Cached markets are restored on app restart

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Polymarket    │───▶│  TypeScript      │───▶│   WebSocket     │
│   WebSocket     │    │  Client          │    │   Server       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                          │
                                                          ▼
                                                ┌─────────────────┐
                                                │   React         │
                                                │   Frontend      │
                                                └─────────────────┘
```

## Setup

### Prerequisites

- Node.js 18+
- pnpm
- Polymarket API credentials

### 1. Install Dependencies

```bash
# Install main project dependencies
pnpm install

# Install frontend dependencies
cd frontend
pnpm install
cd ..
```

### 2. Generate API Credentials

```bash
# Create Python environment
uvx venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install py-clob-client python-dotenv

# Generate API credentials
python generate_api_key.py
```

### 3. Configure Environment

Create `keys.env` with your credentials:

```env
PRIVATE_KEY=0x73a8432219de966cbdac784d7d026e6ce2bb47239dedd9e64381c1ff24379957
CLOB_API_KEY=001307ad-e84d-041c-015c-8362334df839
CLOB_SECRET=Z1eExXDOPOamA58iqMU0ekWQ3QcPk4_1Oy5uvJXadzU=
CLOB_PASSPHRASE=0c17d5684523c36e96555e74cebc6756928972671b5b22ced2dbd674b0dde001
```

## Usage

### Start the WebSocket Server

```bash
# Start the bridge server
node websocket-server.js
```

### Start the Frontend

```bash
# In a new terminal
cd frontend
pnpm dev
```

### Access the Dashboard

Open http://localhost:5173 in your browser to see the real-time dashboard.

### Viewing Logs

All server logs are saved to `polymarket-logs.txt`. Use the helper script to view them:

```bash
# Show last 50 lines
./view-logs.sh tail

# Follow logs in real-time
./view-logs.sh follow

# Search for specific markets
./view-logs.sh grep "Bitcoin"

# Show only deleted markets
./view-logs.sh deleted

# Show last 10 market check cycles
./view-logs.sh check

# Clear logs
./view-logs.sh clear
```

Or view directly:

```bash
# View entire log file
cat polymarket-logs.txt

# Follow logs in real-time
tail -f polymarket-logs.txt

# Search logs
grep "Deleted market" polymarket-logs.txt
```

## Project Structure

```
real-time-data-client/
├── src/                    # TypeScript client source
│   ├── client.ts          # WebSocket client
│   ├── model.ts           # Type definitions
│   └── index.ts           # Main entry point
├── examples/               # Example scripts
│   ├── quick-connection.ts
│   └── all-markets-probability-changes.ts
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom hooks
│   │   ├── db/            # IndexedDB caching
│   │   └── types.ts       # TypeScript types
│   └── package.json
├── websocket-server.js     # Bridge server
├── view-logs.sh           # Log viewer helper script
├── polymarket-logs.txt    # Server logs (auto-generated)
├── generate_api_key.py     # API credential generator
├── keys.env               # Environment variables
└── package.json
```

## API Reference

### WebSocket Messages

The client receives real-time messages with the following structure:

```typescript
interface WebSocketMessage {
    topic: string;
    type: string;
    timestamp: number;
    connection_id: string;
    payload: any;
}
```

### Market Data

```typescript
interface MarketData {
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
}
```

## Configuration

### Category Filtering

The dashboard supports filtering by the following Polymarket categories:

- **All** - Show all markets
- **Trending** - Popular/trending markets
- **Breaking** - Breaking news markets
- **New** - Newly listed markets
- **Politics** - Political events and elections
- **Sports** - Sports events and outcomes
- **Finance** - Financial markets and indicators
- **Crypto** - Cryptocurrency markets
- **Geopolitics** - International relations and conflicts
- **Earnings** - Corporate earnings predictions
- **Tech** - Technology and innovation markets
- **Culture** - Entertainment and cultural events
- **World** - Global events
- **Economy** - Economic indicators and policies
- **Elections** - Election predictions
- **Mentions** - Mention-based markets

Categories are extracted from market data when available, with a fallback to keyword matching on market titles.

### Filtering Options

- **Category filtering**: Filter by Polymarket market categories
- **Delta threshold**: Show all probability changes (no minimum threshold)
- **Market types**: All markets (no filtering)
- **Update frequency**: Real-time WebSocket updates

### Customization

Modify `examples/all-markets-probability-changes.ts` to:

- Change the delta threshold
- Filter specific markets
- Adjust logging format
- Add custom processing logic

## Troubleshooting

### Common Issues

1. **WebSocket connection failed**
    - Check if the bridge server is running
    - Verify port 8080 is available
    - Check firewall settings

2. **No market data**
    - Ensure API credentials are valid
    - Check Polymarket API status
    - Verify network connectivity

3. **Frontend not loading**
    - Check if `pnpm dev` is running
    - Verify port 5173 is available
    - Check browser console for errors

### Logs

- **Client logs**: Check terminal running `node websocket-server.js`
- **Frontend logs**: Check browser developer console
- **TypeScript client**: Check terminal output for WebSocket messages

## Development

### Adding New Features

1. **Backend changes**: Modify TypeScript client in `src/`
2. **Frontend changes**: Update React components in `frontend/src/`
3. **Bridge updates**: Modify `websocket-server.js` for new message types

### Testing

```bash
# Test TypeScript client
pnpm exec ts-node examples/all-markets-probability-changes.ts

# Test frontend
cd frontend
pnpm dev
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:

- Check the troubleshooting section
- Review the logs
- Open an issue on GitHub
