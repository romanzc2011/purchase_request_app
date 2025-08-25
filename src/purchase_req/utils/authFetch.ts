/*
USAGE:
const resp = await authFetch(`/api/getApprovalData`);
*/

export function authFetch(input: RequestInfo, init: RequestInit) {
    const accessToken = localStorage.getItem("access_token");
    const headers = new Headers(init?.headers);
    if (accessToken) {
        headers.set("Authorization", `Bearer ${accessToken}`);
    }
    headers.set("Accept", "application/json");

    return fetch(input, { ...init, headers });
}
