import StatusBadge from "./StatusBadge"

interface HeaderProps {
  isOnline: boolean
}

export default function Header({ isOnline }: HeaderProps) {
  return (
    <div className="flex items-center space-x-4 mb-6">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">IA SEI</h1>
      <StatusBadge isOnline={isOnline} />
    </div>
  )
}