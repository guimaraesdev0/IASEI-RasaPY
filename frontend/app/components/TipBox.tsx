interface TipBoxProps {
  icon: string
  title: string
  description: string
}

export default function TipBox({ icon, title, description }: TipBoxProps) {
  return (
    <div className="bg-white/50 dark:bg-gray-800/50 p-4 rounded-lg shadow-md hover:bg-white/70 dark:hover:bg-gray-700/70 transition-all duration-200">
      <div className="text-3xl mb-2">{icon}</div>
      <h3 className="text-lg font-semibold mb-1 text-gray-900 dark:text-white">{title}</h3>
      <p className="text-sm text-gray-700 dark:text-gray-300">{description}</p>
    </div>
  )
}

