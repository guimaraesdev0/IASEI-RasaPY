import { NextResponse } from "next/server";
import WebSocket from "ws"; // Usando o WebSocket nativo do Node.js

export async function GET() {
  return new Promise((resolve) => {
    const socket = new WebSocket("ws://156.67.27.152:5005/socket.io/?EIO=4&transport=websocket");

    // Quando a conexão for estabelecida, o servidor está online
    socket.on("open", () => {
      resolve(NextResponse.json({ isOnline: true }));
      socket.close(); // Fecha a conexão imediatamente após a verificação
    });

    // Quando a conexão falhar ou for fechada, o servidor está offline
    socket.on("error", () => {
      resolve(NextResponse.json({ isOnline: false }));
    });

    socket.on("close", () => {
      resolve(NextResponse.json({ isOnline: false }));
    });
  });
}
