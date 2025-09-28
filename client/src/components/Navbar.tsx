import { Link } from "react-router-dom";
import { type User } from "../api/useFetchUser";

export const Navbar = ({ user, onLogout }: { user: User | null, onLogout?: () => void }) => {
  return (
    <nav className="flex items-center justify-between px-8 py-4 bg-gray-800 text-white">
      <div className="text-2xl font-bold text-purple-400">
        <Link to="/">StopJudol</Link>
      </div>

      {user ? (
        <div className="relative group">
          <button className="flex items-center space-x-2 bg-gray-700 px-4 py-2 rounded hover:bg-gray-600">
            <span>{user.custom_url || user.name}</span>
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M5.5 7l4.5 4.5L14.5 7" />
            </svg>
          </button>
          <div className="absolute right-0 mt-2 bg-gray-700 rounded shadow-lg hidden group-hover:block min-w-[200px] z-10">
            <div className="px-4 py-2 text-sm text-gray-300 border-b border-gray-600">
              <p><strong>{user.name}</strong></p>
              <p>{user.email}</p>
            </div>
            <button
              onClick={onLogout}
              className="block w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-gray-600"
            >
              Logout
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => window.location.href = "http://localhost:8000/auth/login"}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded"
        >
          Login
        </button>
      )}
    </nav>
  );
};