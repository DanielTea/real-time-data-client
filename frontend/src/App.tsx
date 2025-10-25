import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { JsonView } from "./pages/JsonView";
import { Analytics } from "./pages/Analytics";
import { TradingChat } from "./pages/TradingChat";
import { AutoTrading } from "./pages/AutoTrading";
import { Settings } from "./pages/Settings";
import { About } from "./pages/About";

function App() {
    return (
        <Router>
            <Layout>
                <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/json" element={<JsonView />} />
                    <Route path="/analytics" element={<Analytics />} />
                    <Route path="/trading" element={<TradingChat />} />
                    <Route path="/autotrading" element={<AutoTrading />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="/about" element={<About />} />
                </Routes>
            </Layout>
        </Router>
    );
}

export default App;
