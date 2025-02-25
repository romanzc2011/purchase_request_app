import { v4 as uuidv4 } from "uuid";

export class FetchService {
    url: string;
    method: string;
    headers: HeadersInit;

    constructor(url: string, method: string, headers: HeadersInit) {
        this.url = url;
        this.method = method;
        this.headers = headers;
    }

    /*************************************************************************/
    /* MAKE REQUEST FUNCTION */
    /*************************************************************************/
    async makeRequest(
        body?: any,
        setIsSubmitted?: (value: boolean) => void,
        setReqID?: (id: string) => void
    ): Promise<Response> {
        const response = await fetch(this.url, {
            method: this.method,
            headers: this.headers,
            body: body ? JSON.stringify(body) : undefined,
        });

        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }

        // Call the set callbacks if provided
        if (setIsSubmitted) {
            setIsSubmitted(true);
        }

        if (setReqID) {
            setReqID(uuidv4());
        }
        return response;
    }
}
