import { useState } from "react";
import api from "../services/api";

export default function Chat() {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState("");

  const sendMessage = async () => {
    if (!message.trim()) return;

    try {
      const res = await api.post("/chat/message", { message });
      setResponse(res.data.response);
    } catch (error) {
      setResponse("Erro ao conectar com a API.");
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: "40px auto", fontFamily: "Arial" }}>
      <h1>Food Delivery Assistant</h1>

      <textarea
        placeholder="Digite sua mensagem..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        style={{ width: "100%", height: 100 }}
      />

      <button
        style={{ marginTop: 10, padding: "8px 16px" }}
        onClick={sendMessage}
      >
        Enviar
      </button>

      {response && (
        <div style={{ background: "#eee", padding: 16, marginTop: 20 }}>
          <strong>Resposta do chatbot:</strong>
          <p>{response}</p>
        </div>
      )}
    </div>
  );
}
