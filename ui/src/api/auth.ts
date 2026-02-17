import {api} from "./client.ts";

export async function login(username: string, password:string) {
    const params = new URLSearchParams();
    params.append("username", username);
    params.append("password", password);

    const res = await api.post("/auth/login", params);

    return res;
}