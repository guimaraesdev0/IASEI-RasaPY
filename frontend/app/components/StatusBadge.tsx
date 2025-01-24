import { useState, useEffect } from "react"

interface StatusBadgeProps {
  isOnline: boolean
}

export default function StatusBadge({ isOnline }: StatusBadgeProps) {
  return (
    <div className="flex items-center">
      <div className={`w-3 h-3 rounded-full mr-2 ${isOnline ? "bg-green-500" : "bg-red-500"}`}></div>
      <span className="text-sm font-medium">{isOnline ? "Online" : "Offline"}</span>
    </div>
  )
}

