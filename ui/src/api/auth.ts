import {api} from "./client.ts";
import {getToken, setToken} from "./token.ts";

export async function login(username: string, password:string) {
    const params = new URLSearchParams();
    params.append("username", username);
    params.append("password", password);

    const res = await api.post("/auth/login", params);

    return res.data;
}

export async function refreshAccessToken() {
    const refreshToken = await getToken("refresh");

    const res = await api.post("/auth/refresh", {
        refresh_token: refreshToken,
    });

    setToken("access", res.data.access_token);

    return res.data.access_token;
}