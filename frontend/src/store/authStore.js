import { create } from "zustand";
import { persist } from "zustand/middleware";
 
/** Login state. `persist` keeps it in localStorage so a refresh doesn't log you out. */
export const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      user: null,
      setSession: ({ access_token, user }) => set({ token: access_token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: "fincrew-auth" }
  )
);
 