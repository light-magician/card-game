import React, { useState } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

function App() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);

  const handleSearch = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/cards/search?query=${encodeURIComponent(searchQuery)}`,
      );
      if (!response.ok) {
        throw new Error("Search failed");
      }
      const data = await response.json();
      setSearchResults(data);
    } catch (error) {
      console.error("Error searching cards:", error);
      // Add error handling UI here
    }
  };

  return (
    <div className="container mx-auto p-4">
      <div className="flex gap-2 mb-4">
        <Input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search cards..."
          className="flex-1"
        />
        <Button onClick={handleSearch}>Search</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {searchResults.map((card) => (
          <Card key={card.id} className="p-4">
            <div className="flex flex-col gap-2">
              <h2 className="text-xl font-bold">{card.name}</h2>
              {card.card_images && card.card_images[0] && (
                <img
                  src={card.card_images[0].image_url_small}
                  alt={card.name}
                  className="w-full object-contain"
                />
              )}
              <p className="text-sm text-gray-600">{card.desc}</p>
              {card.atk !== null && card.def_ !== null && (
                <p className="text-sm">
                  ATK: {card.atk} / DEF: {card.def_}
                </p>
              )}
              {card.attribute && (
                <p className="text-sm">Attribute: {card.attribute}</p>
              )}
              {card.level && <p className="text-sm">Level: {card.level}</p>}
              {card.type_field && (
                <p className="text-sm">Type: {card.type_field}</p>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default App;
