import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu"
import { type User } from "../api/useFetchUser"
import { Link } from "react-router-dom"

export const UserDropdown = ({
  user,
  onLogout,
}: {
  user: User
  onLogout?: () => void
}) => {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center space-x-2 bg-gray-700 px-4 py-2 rounded hover:bg-gray-600">
          <span>{user.custom_url || user.name}</span>
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M5.5 7l4.5 4.5L14.5 7" />
          </svg>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56 bg-gray-800 text-white border border-gray-700">
        <DropdownMenuLabel>
          <div className="flex flex-col">
            <span className="font-medium">{user.name}</span>
            <span className="text-sm text-gray-400">{user.email}</span>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link to="/dashboard" className="w-full">
            Dashboard
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={onLogout}
          className="text-red-400 hover:bg-gray-700"
        >
          Logout
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
