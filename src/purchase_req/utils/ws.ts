export function computerWSURL(path = "/communicate") { 
    if (
        (window.location.protocol === "http:") || 
        (window.location.protocol === "https:") || 
        (window.location.protocol === "wss:") || 
        (window.location.protocol === "ws:")
    ) {
        const proto = window.location.protocol;
        return `${proto}//${window.location.host}${path}`;
    }

    return path;
}