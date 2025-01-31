const http = require("http");
const socketIo = require("socket.io");
const express = require("express");
const app = express();
import { NextResponse } from "next/server"
import { Socket } from "socket.io-client" // Importe o tipo correto para o socket
const server = http.createServer(app);
const io = socketIo(server);

io.on("connection", (socket) => {
  console.log("Usuário conectado");

  socket.on("user_uttered", async (data) => {
    try {
      const response = await fetch("http://localhost:5005/webhooks/rest/webhook", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: data.message }),
      });
      const botResponse = await response.json();
      socket.emit("bot_uttered", { text: botResponse[0]?.text || "Desculpe, não entendi." });
    } catch (error) {
      console.error("Erro:", error);
      socket.emit("bot_uttered", { text: "Ocorreu um erro ao processar sua solicitação." });
    }
  });

  socket.on("disconnect", () => {
    console.log("Usuário desconectado");
  });
});

server.listen(5005, () => {
  console.log("Servidor WebSocket rodando na porta 5005");
});
