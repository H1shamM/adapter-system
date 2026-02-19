import axios from "axios"
import {clearToken, getToken} from "./token.ts";
import {refreshAccessToken} from "./auth.ts";

export const api = axios.create({
    baseURL: "http://localhost:8000/api/v1",
})

api.interceptors.request.use((config) => {
    const token = getToken("access")

    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true

            try {
                const newAccessToken = await refreshAccessToken();

                originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;

                return api(originalRequest);
            } catch (refreshError) {
                console.log("Refresh Failed -> logout", refreshError);
                clearToken("access");
                clearToken("refresh");

                window.location.href = "/login";
            }
        }

        return Promise.reject(error);
    }
);

