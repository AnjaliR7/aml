import React, { useEffect, useState } from "react";

const Dashboard = () => {
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:5000/transactions")
      .then((response) => response.json())
      .then((data) => setTransactions(data))
      .catch((error) => console.error("Error fetching transactions:", error));
  }, []);

  return (
    <div className="bg-gray-900 text-white min-h-screen p-6">
      <h1 className="text-3xl font-bold mb-4">Admin - Anti-Money Laundering Application</h1>
      <h2 className="text-xl mb-4">All Transactions</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-gray-800 border border-gray-700">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="p-2">ID</th>
              <th className="p-2">Amount</th>
              <th className="p-2">Payment Currency</th>
              <th className="p-2">Received Currency</th>
              <th className="p-2">Sender Bank</th>
              <th className="p-2">Receiver Bank</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx) => (
              <tr key={tx[0]} className="border-b border-gray-700">
                <td className="p-2">{tx[0]}</td>
                <td className="p-2">{tx[6]}</td>
                <td className="p-2">{tx[1]}</td>
                <td className="p-2">{tx[2]}</td>
                <td className="p-2">{tx[3]}</td>
                <td className="p-2">{tx[4]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Dashboard;
