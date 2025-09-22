
export const HomePage = () => {
    return (
        <div className="min-h-screen bg-gray-900 text-white">
            <nav className="flex items-center justify-between px-8 py-4 bg-gray-800">
                <div className="text-2xl font-bold text-purple-400">StopJudol</div>
                <button
                onClick={() => window.location.href = "http://localhost:8000/auth/login"}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded"
                >
                Login
                </button>
            </nav>

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