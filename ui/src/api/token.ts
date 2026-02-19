export function setToken(name: string,token: string) {
    localStorage.setItem(name, token);
}

export function getToken(name: string) {
    return localStorage.getItem(name);
}

export function clearToken(name: string) {
    localStorage.removeItem(name);
}