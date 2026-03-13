import { BrowserRouter, Routes, Route } from "react-router-dom";
import Chat from "./pages/chat";
import Restaurants from "./pages/restaurants";
import Home from "./pages/Home";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/restaurants" element={<Restaurants />} />
      </Routes>
    </BrowserRouter>
  );
}
