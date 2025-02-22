import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Camera } from 'lucide-react';

const TradingDashboard = () => {
  const [decisions, setDecisions] = useState([]);
  const [metrics, setMetrics] = useState(null);
  
  useEffect(() => {
    // In a real implementation, this would load from your trading_decisions JSON files
    // For demo, using sample data
    const sampleDecisions = [
      {
        action: "BUY",
        ticker: "NVDA",
        amount: 100,
        expected_profit_percentage: 2.5,
        confidence: 0.85,
        reasoning: "AI demand signals strong momentum",
        timestamp: "2025-01-14"
      },
      {
        action: "SELL",
        ticker: "AAPL",
        amount: 50,
        expected_profit_percentage: 1.8,
        confidence: 0.75,
        reasoning: "Technical indicators suggest short-term resistance",
        timestamp: "2025-01-14"
      }
    ];
    
    setDecisions(sampleDecisions);
    
    // Calculate summary metrics
    const summaryMetrics = {
      totalTrades: sampleDecisions.length,
      buyCount: sampleDecisions.filter(d => d.action === "BUY").length,
      sellCount: sampleDecisions.filter(d => d.action === "SELL").length,
      avgConfidence: sampleDecisions.reduce((acc, d) => acc + d.confidence, 0) / sampleDecisions.length,
      avgExpectedProfit: sampleDecisions.reduce((acc, d) => acc + d.expected_profit_percentage, 0) / sampleDecisions.length
    };
    
    setMetrics(summaryMetrics);
  }, []);

  return (
    <div className="w-full max-w-6xl mx-auto p-4 space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Total Trades</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.totalTrades || 0}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Avg Confidence</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(metrics?.avgConfidence * 100 || 0).toFixed(1)}%
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Avg Expected Profit</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(metrics?.avgExpectedProfit || 0).toFixed(1)}%
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Trading Decisions Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Trading Decisions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="p-2 text-left">Action</th>
                  <th className="p-2 text-left">Ticker</th>
                  <th className="p-2 text-right">Amount</th>
                  <th className="p-2 text-right">Expected Profit</th>
                  <th className="p-2 text-right">Confidence</th>
                  <th className="p-2">Reasoning</th>
                </tr>
              </thead>
              <tbody>
                {decisions.map((decision, idx) => (
                  <tr key={idx} className="border-b">
                    <td className="p-2">
                      <span className={`inline-block px-2 py-1 rounded ${
                        decision.action === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {decision.action}
                      </span>
                    </td>
                    <td className="p-2">{decision.ticker}</td>
                    <td className="p-2 text-right">{decision.amount}</td>
                    <td className="p-2 text-right">{decision.expected_profit_percentage}%</td>
                    <td className="p-2 text-right">{(decision.confidence * 100).toFixed(1)}%</td>
                    <td className="p-2">{decision.reasoning}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TradingDashboard;