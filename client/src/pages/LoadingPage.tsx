import { Navbar } from "../components/Navbar";

export const LoadingPage = () => {
  return (
    <div className="min-h-screen bg-gray-900 text-white min-w-screen">
      <Navbar user={null} />
    </div>
  );
};
