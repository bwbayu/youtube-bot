import { Routes, Route } from "react-router";
import { DashboardPage } from './pages/DashboardPage'
import { HomePage } from "./pages/HomePage";
import { NotFoundPage } from "./pages/NotFoundPage";

function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/home" element={<HomePage />} />  
        <Route path="*" element={<NotFoundPage />} />  
      </Routes>      
    </>
  );
}

export default App;