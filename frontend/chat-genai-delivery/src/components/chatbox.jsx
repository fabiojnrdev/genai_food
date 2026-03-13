import { use, useState } from "react";
import { SendMessage } from "../client";
import MessageBubble from "./MessageBubble";

export default function ChatBox(){
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    
    async function handleSend() {
        if (!input.trim()) return;
         const userMsg = { sender: "user", text: input };
    setMessages(prev => [...prev, userMsg]);

    const res = await sendMessage(input);

    const botMsg = { sender: "bot", text: res.response };
    setMessages(prev => [...prev, botMsg]);

    setInput("");
    }
}

