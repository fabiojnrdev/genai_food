import { useEffect, useState } from "react";
import { getRestaurants } from "../api/client";
import RestaurantCard from "../components/restaurantcard";

export default function Restaurants() {
  const [restaurants, setRestaurants] = useState([]);

  useEffect(() => {
    async function load() {
      const data = await getRestaurants();
      setRestaurants(data);
    }
    load();
  }, []);

  return (
    <div style={{ padding: "20px" }}>
      <h1>Restaurantes</h1>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "16px" }}>
        {restaurants.map((r, i) => (
          <RestaurantCard key={i} restaurant={r} />
        ))}
      </div>
    </div>
  );
}
