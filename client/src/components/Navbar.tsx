import { Link } from "react-router-dom";
import { type User } from "../api/useFetchUser";
import { UserDropdown } from "./UserDropdown";

export const Navbar = ({ user, onLogout }: { user: User | null, onLogout?: () => void }) => {
  return (
    <nav className="flex items-center justify-between px-8 py-4 bg-gray-800 text-white">
      <div className="text-2xl font-bold text-purple-400">
        <Link to="/dashboard">StopJudol</Link>
      </div>

      {user ? (
        <UserDropdown user={user} onLogout={onLogout} />
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
