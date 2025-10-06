import { Routes, Route } from "react-router";
import { DashboardPage } from './pages/DashboardPage'
import { HomePage } from "./pages/HomePage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { VideoDetailPage } from "./pages/VideoDetailPage";
import { LoadingPage } from "./pages/LoadingPage";
import { useFetchUser } from "./api/useFetchUser";
import { UserContext } from "./context/UserContext";

function App() {
  const { user, loadingUser } = useFetchUser();

  if (loadingUser) {
    return <LoadingPage />;
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    );
  }

  return (
    <UserContext.Provider value={user}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />  
        <Route path="/video/:videoId" element={<VideoDetailPage />} />  
        <Route path="*" element={<NotFoundPage />} />  
      </Routes>      
    </UserContext.Provider>
  );
}

export default App;
