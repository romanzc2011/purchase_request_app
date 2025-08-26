import { fetchUsernames } from "../../utils/misc_utils";
import { useQuery } from "@tanstack/react-query";

export function useUsernames(query: string) {
    return useQuery({
        queryKey: ["usernames", query],
        queryFn: () => fetchUsernames(query),
        enabled: query.length >= 2,
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}