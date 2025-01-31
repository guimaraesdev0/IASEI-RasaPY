import { useState, useEffect } from "react"

interface StatusBadgeProps {
  isOnline: boolean
}

export default function StatusBadge({ isOnline }: StatusBadgeProps) {
  const [status, setStatus] = useState<{ color: string; text: string }>({
    color: "bg-gray-500",
    text: "Conectando...",
  })

  useEffect(() => {
    const timeout = setTimeout(() => {
      setStatus({
        color: isOnline ? "bg-green-500" : "bg-red-500",
        text: isOnline ? "Online" : "Offline",
      })
    }, 2000) // Simula um delay de conexão

    return () => clearTimeout(timeout)
  }, [isOnline])

  return (
    <div className="flex items-center">
      <div className={`w-3 h-3 rounded-full mr-2 ${status.color}`}></div>
      <span className="text-sm font-medium">{status.text}</span>
    </div>
  )
}
