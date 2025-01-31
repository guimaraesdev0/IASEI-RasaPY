"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send } from "lucide-react"
import Message from "./components/Message"
import Header from "./components/Header"
import TipBox from "./components/TipBox"
import { ThemeToggle } from "@/components/theme-toggle"
import io, { Socket } from "socket.io-client"

interface MessageType {
  text: string
  isUser: boolean
  isLoading?: boolean
}

export default function Chat() {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [messages, setMessages] = useState<MessageType[]>([])
  const [input, setInput] = useState("")
  const [isOnline, setIsOnline] = useState(false)

  useEffect(() => {
    const socketConnection = io("https://iaseibackend.duckdns.org")
    setSocket(socketConnection)

    socketConnection.on("connect", () => {
      console.log("Conectado ao servidor Rasa!")
      setIsOnline(true)
    })

    socketConnection.on("disconnect", () => {
      console.log("Desconectado do servidor Rasa.")
      setIsOnline(false)
    })

    return () => {
      if (socketConnection) {
        socketConnection.disconnect()
      }
    }
  }, [])

  const sendMessage = () => {
    if (input.trim() === "" || !socket) return;
  
    // Processar quebras de linha e tabelas
    const processedInput = input
      .replace(/\\n/g, '') // Converter \n para quebras reais
      .replace(/\|/g, ''); // Adicionar espaço após pipes
  
    const newMessages = [
      ...messages,
      { text: input, isUser: true },
      { text: "´Processando...", isUser: false, isLoading: true }
    ];
    
    setMessages(newMessages);
    setInput("");
  
    socket.emit("user_uttered", { message: input });
  
    const responseHandler = (data: any) => {
      console.log("Mensagem recebida do Rasa:", data);

      
      const formattedText = data.text
        .replaceAll("/n", "\n")
        .replace(/\|/g, '| ');
  
      setMessages((prev) => {
        const newMessages = [...prev];
        const loadingIndex = newMessages.findIndex(msg => msg.isLoading);
        if (loadingIndex !== -1) {
          newMessages[loadingIndex] = { text: formattedText, isUser: false };
        }
        return newMessages;
      });
  
      socket.off("bot_uttered", responseHandler);
    };
  
    socket.on("bot_uttered", responseHandler);
  };

  return (
    <div className="flex flex-col h-screen bg-white dark:bg-black text-gray-900 dark:text-gray-100">
      <div className="absolute inset-0 bg-tailwindBlue opacity-5 dark:opacity-5 blur-3xl"></div>
      <div className="relative z-10 flex flex-col h-full p-6">
        <div className="flex justify-between items-center mb-4">
          <Header isOnline={isOnline} />
          <ThemeToggle />
        </div>
        <Card className="flex-grow mb-4 bg-white/50 dark:bg-black/50 border-gray-200 dark:border-gray-800 overflow-hidden backdrop-blur-sm">
          <ScrollArea className="h-full p-6">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center">
                <div className="grid grid-cols-2 gap-6 w-full max-w-4xl px-4">
                  <TipBox icon="💡" title="Pesquisa por Processos" description="Solicite à IA a pesquisa de processos específicos." />
                  <TipBox icon="🔍" title="Pesquisa por Interessados" description="A IA pode retornar todos os processos e documentos relacionados a um interessado." />
                  <TipBox icon="📊" title="Estatísticas" description="Solicite análises detalhadas de documentos e processos com base em dados estatísticos." />
                  <TipBox icon="📅" title="Pesquisa por Data" description="Realize pesquisas utilizando filtros de datas para processos e documentos." />
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message, index) => (
                  <Message
                    key={index}
                    text={message.text}
                    isUser={message.isUser}
                    isLoading={message.isLoading}
                  />
                ))}
              </div>
            )}
          </ScrollArea>
        </Card>
        <div className="flex mx-auto w-full">
          <Input
            className="flex-grow mr-2 bg-white/50 dark:bg-gray-800/50 border-gray-300 dark:border-gray-700 text-gray-900 dark:text-white backdrop-blur-sm"
            placeholder="Digite sua mensagem..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && sendMessage()}
          />
          <Button className="bg-blue-600 hover:bg-blue-900 text-white" onClick={sendMessage}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
