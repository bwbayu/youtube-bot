import { useUser } from "../context/UserContext";
import { Navbar } from "../components/Navbar";

export const HomePage = () => {
    const user = useUser();
    return (
        <div className="min-h-screen bg-gray-900 text-white">
            <Navbar user={user} />

            <main className="flex flex-col md:flex-row items-center md:items-start px-8 py-16">
                <div className="w-full md:w-1/2">
                    <h1 className="text-4xl font-bold text-green-400 mb-4">
                        Keep Your YouTube Clean With Our Bot!
                    </h1>
                    <p className="text-gray-300 mb-6">
                        Introducing a machine-learning-powered YouTube bot that detects and deletes
                        online gambling comments. Unlike manual moderation or rule-based filters, this
                        AI bot uses NLP to understand various tricks used by gambling promoters,
                        ensuring a cleaner and safer YouTube environment.
                    </p>
                    <div className="flex space-x-4">
                    </div>
                </div>
                {/* <div className="hidden md:block md:w-1/2 h-64 bg-gray-800 rounded-lg ml-8">
                </div> */}
            </main>
        </div>
    )
}