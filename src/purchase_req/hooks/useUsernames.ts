import { useQuery } from "@tanstack/react-query";
import { fetchUsernames } from "../utils/misc_utils";

export function useUsernames(query: string) {
    return useQuery({
        queryKey: ["usernames", query],
        queryFn: () => fetchUsernames(query),
        enabled: Boolean(query),
        staleTime: 5_000
    });
}