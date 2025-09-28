// src/context/UserContext.tsx
import { createContext, useContext } from "react";

export const UserContext = createContext<any>(null);
export const useUser = () => useContext(UserContext);