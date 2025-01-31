import { Card } from "@/components/ui/card"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

interface MessageProps {
  text: string
  isUser: boolean
  isLoading?: boolean
}

export default function Message({ text, isUser, isLoading }: MessageProps) {
  // Função para verificar se o texto contém HTML
  const isHTML = (str: string) => {
    const doc = new DOMParser().parseFromString(str, "text/html")
    return doc.body.childNodes.length > 0
  }

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-2`}>
      {isLoading ? (
        // Caso esteja carregando, a mensagem fica fora da bolha de chat
        <div className="flex items-center space-x-2 justify-center text-lg text-gray-500 dark:text-gray-300">
          <span className="animate-pulse">Processando...</span>
        </div>
      ) : (
        <Card
          className={`p-2 max-w-[40%] ${
            isUser
              ? "bg-blue-500 dark:bg-blue-700 text-white rounded-tl-1xl rounded-tr-2xl rounded-bl-2xl"
              : "bg-gray-200 dark:bg-gray-600 text-gray-900 dark:text-white rounded-tl-2xl rounded-tr-2xl rounded-br-2xl"
          } backdrop-blur-sm`}
        >
          {isHTML(text) ? (
            // Caso a mensagem seja HTML, renderiza diretamente
            <div
              className="text-lg whitespace-pre-wrap"
              dangerouslySetInnerHTML={{ __html: text }}
            />
          ) : (
            // Caso a mensagem seja Markdown
            <ReactMarkdown
              className="text-lg whitespace-pre-wrap"
              remarkPlugins={[remarkGfm]}
              components={{
                table: ({ node, ...props }) => (
                  <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700 my-2">
                    <table {...props} className="w-full border-collapse" />
                  </div>
                ),
                th: ({ node, ...props }) => (
                  <th
                    {...props}
                    className="px-4 py-2 border-b-2 border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-left"
                  />
                ),
                td: ({ node, ...props }) => (
                  <td {...props} className="px-4 py-2 border-b border-gray-100 dark:border-gray-700" />
                ),
                tr: ({ node, ...props }) => (
                  <tr {...props} className="even:bg-gray-50 dark:even:bg-gray-800/50" />
                )
              }}
            >
              {text}
            </ReactMarkdown>
          )}
        </Card>
      )}
    </div>
  )
}
