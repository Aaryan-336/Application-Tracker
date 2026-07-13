const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

function getHeaders(isMultipart = false) {
    const headers: Record<string, string> = {};
    if (!isMultipart) {
        headers["Content-Type"] = "application/json";
    }
    if (typeof window !== "undefined") {
        const token = localStorage.getItem("career_agent_token");
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
    }
    return headers;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const isMultipart = options.body instanceof FormData;
    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers: {
            ...getHeaders(isMultipart),
            ...options.headers,
        },
    });

    if (!response.ok) {
        let errorMessage = "An error occurred";
        try {
            const errData = await response.json();
            errorMessage = errData.detail || errorMessage;
        } catch {
            errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
    }

    if (response.status === 204) {
        return {} as T;
    }

    return response.json();
}

export const api = {
    // Auth endpoints
    register: (email: string, password: string) => 
        request<{ id: string; email: string }>("/auth/register", {
            method: "POST",
            body: JSON.stringify({ email, password }),
        }),

    login: (email: string, password: string) =>
        request<{ access_token: string; token_type: string }>("/auth/login", {
            method: "POST",
            body: JSON.stringify({ email, password }),
        }),

    getMe: () => 
        request<{
            id: string;
            email: string;
            full_name?: string;
            preferred_roles?: string[];
            preferred_locations?: string[];
            salary_expectation?: number;
        }>("/auth/me"),

    updateProfile: (profile: {
        full_name?: string;
        preferred_roles?: string[];
        preferred_locations?: string[];
        salary_expectation?: number;
    }) =>
        request<any>("/auth/profile", {
            method: "PUT",
            body: JSON.stringify(profile),
        }),

    // Resume endpoints
    uploadResume: (formData: FormData) =>
        request<{
            id: string;
            filename: string;
            skills: string[];
            experience: any[];
            education: any[];
            preferred_roles: string[];
            created_at: string;
        }>("/resume/upload", {
            method: "POST",
            body: formData,
        }),

    getResume: () =>
        request<{
            id: string;
            filename: string;
            skills: string[];
            experience: any[];
            education: any[];
            preferred_roles: string[];
            created_at: string;
        }>("/resume/me"),

    // Jobs endpoints
    getMatches: (status?: string, minScore = 0) => {
        let path = "/jobs/matches";
        const params: string[] = [];
        if (status) params.push(`status=${status}`);
        if (minScore > 0) params.push(`min_score=${minScore}`);
        if (params.length > 0) path += `?${params.join("&")}`;
        return request<any[]>(path);
    },

    triggerDiscovery: (query?: string | boolean, location?: string, limit?: number, sources?: string, useMock = false) => {
        let actualQuery = "Software Engineer";
        let actualLocation = "Remote";
        let actualLimit = 10;
        let actualUseMock = useMock;
        let actualSources = sources || "";

        if (typeof query === "boolean") {
            actualUseMock = query;
        } else if (query) {
            actualQuery = String(query);
        }
        
        if (location && location !== "undefined") {
            actualLocation = location;
        }
        if (limit && !isNaN(Number(limit))) {
            actualLimit = Number(limit);
        }

        let url = `/jobs/discover?query=${encodeURIComponent(actualQuery)}&location=${encodeURIComponent(actualLocation)}&limit=${actualLimit}&use_mock=${actualUseMock}`;
        if (actualSources) {
            url += `&sources=${encodeURIComponent(actualSources)}`;
        }
        return request<{ message: string; new_jobs_discovered: number }>(url, {
            method: "POST",
        });
    },

    // Gmail sync endpoints
    connectGmail: (gmail_address: string, gmail_app_password: string) =>
        request<any>("/gmail/connect", {
            method: "POST",
            body: JSON.stringify({ gmail_address, gmail_app_password }),
        }),

    getGmailStatus: () =>
        request<{
            is_connected: boolean;
            gmail_address?: string;
            gmail_last_synced?: string;
        }>("/gmail/status"),

    syncGmail: (daysBack = 14) =>
        request<{
            message: string;
            updates_count: number;
            updates: any[];
        }>(`/gmail/sync?days_back=${daysBack}`, {
            method: "POST",
        }),

    // Application tracking endpoints
    getTrackedApplications: () =>
        request<any[]>("/applications/tracker"),

    updateStatus: (userJobId: string, status: string, notes?: string) =>
        request<any>(`/applications/${userJobId}/status`, {
            method: "PUT",
            body: JSON.stringify({ status, notes }),
        }),

    getDashboardStats: () =>
        request<{
            totalMatches: number;
            discoveredCount: number;
            appliedCount: number;
            interviewCount: number;
            offerCount: number;
            rejectedCount: number;
            avgMatchScore: number;
            responseRate: number;
        }>("/applications/dashboard-stats"),
};
