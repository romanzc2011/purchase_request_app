import axios from "axios";

const PROD_URL = `https://${window.location.hostname}:5002`;
const DEV_URL = `http://${window.location.hostname}:5004`;
export default axios.create({
    baseURL: DEV_URL,
    headers: {
        "Content-Type": "application/json",
    },
});