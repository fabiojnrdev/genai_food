export default function MessageBubble({ sender, text }) {
  const isUser = sender === "user";

  return (
    <div
      style={{
        textAlign: isUser ? "right" : "left",
        marginBottom: "8px"
      }}
    >
      <span
        style={{
          padding: "10px 14px",
          borderRadius: "12px",
          background: isUser ? "#201b76ff" : "#c6c7c9ff",
          color: isUser ? "white" : "black",
          display: "inline-block",
          maxWidth: "68%"
        }}
      >
        {text}
      </span>
    </div>
  );
}
