import axios from "axios";

export default axios.create({
    baseURL: `https://${window.location.hostname}:5002`,
    headers: {
        "Content-Type": "application/json",
    },
});