const API_BASE_URL = "http://localhost:8000/api";

export function getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("sage_token");
}

export function setToken(token: string) {
    if (typeof window !== "undefined") {
        localStorage.setItem("sage_token", token);
    }
}

export function clearToken() {
    if (typeof window !== "undefined") {
        localStorage.removeItem("sage_token");
    }
}

async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
    const token = getToken();
    const headers = {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
    });

    if (response.status === 401) {
        clearToken();
        if (typeof window !== "undefined" && window.location.pathname !== "/login") {
            window.location.href = "/login";
        }
        throw new Error("Unauthorized - session expired");
    }

    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "API request failed");
    }

    return data;
}

export const api = {
    // --- Auth ---
    register: (userData: any) => fetchWithAuth("/auth/register", {
        method: "POST",
        body: JSON.stringify(userData),
    }),

    // Note: OAuth2 expects form-urlencoded data for login
    login: async (credentials: any) => {
        const formData = new URLSearchParams();
        formData.append("username", credentials.email);
        formData.append("password", credentials.password);

        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: formData.toString(),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Login failed");
        return data;
    },

    // --- Users ---
    getMe: () => fetchWithAuth("/users/me"),

    // --- Activities ---
    getActivities: () => fetchWithAuth("/users/me/activities"),

    logActivity: (activity: any) => fetchWithAuth("/users/me/activities", {
        method: "POST",
        body: JSON.stringify(activity),
    })
};
