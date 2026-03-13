export default function RestaurantCard({ restaurant }) {
  return (
    <div
      style={{
        padding: "16px",
        borderRadius: "8px",
        background: "#f9fafb",
        boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
      }}
    >
      <h2>{restaurant.name}</h2>
      <p>{restaurant.category}</p>
      <p>⭐ {restaurant.rating}</p>
    </div>
  );
}
