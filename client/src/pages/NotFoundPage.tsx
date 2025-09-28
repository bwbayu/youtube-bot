import { Link } from "react-router-dom";
import { Navbar } from "../components/Navbar";
import { useUser } from "../context/UserContext";

export const NotFoundPage = () => {
  const user = useUser();

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col">
      <Navbar user={user} />
      <main className="flex-grow flex items-center justify-center px-4">
        <div className="text-center">
          <h1 className="text-6xl font-bold text-red-500 mb-4">404</h1>
          <p className="text-xl mb-6 text-gray-300">Halaman yang kamu cari tidak ditemukan.</p>
          <Link
            to="/"
            className="inline-block px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
          >
            Kembali ke Beranda
          </Link>
        </div>
      </main>
    </div>
  );
};
