import { Card } from "@/components/ui/card"
import ReactMarkdown from "react-markdown"

interface MessageProps {
  text: string
  isUser: boolean
}

export default function Message({ text, isUser }: MessageProps) {
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-2`}>
      <Card
        className={`p-3 max-w-[50%] ${
          isUser
            ? "bg-blue-500 dark:bg-blue-700 text-white rounded-tl-1xl rounded-tr-2xl rounded-bl-2xl"
            : "bg-gray-200 dark:bg-gray-600 text-gray-900 dark:text-white rounded-tl-2xl rounded-tr-2xl rounded-br-2xl"
        } backdrop-blur-sm`}
      >
        {/* Renderiza o texto como Markdown */}
        <ReactMarkdown className="text-lg">{text}</ReactMarkdown>
      </Card>
    </div>
  )
}