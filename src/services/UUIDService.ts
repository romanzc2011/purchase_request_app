import { useQuery, useQueryClient } from "@tanstack/react-query";

export const useUUIDStore = () => {
    const queryClient = useQueryClient();
    
    // Get UUIDs from the query cache
    const { data: uuids = {} } = useQuery<Record<string, string>>({
        queryKey: ['uuids'],
        queryFn: () => ({}),
        staleTime: Infinity,
    });
    
    // Set a UUID for a specific ID
    const setUUID = (id: string, uuid: string) => {
        console.log(`Setting UUID for ID ${id}: ${uuid}`);
        queryClient.setQueryData(['uuids'], (oldData: Record<string, string> = {}) => {
            const newData = {
                ...oldData,
                [id]: uuid
            };
            console.log("Updated UUID store:", newData);
            return newData;
        });
    };
    
    // Get a UUID for a specific ID
    const getUUID = (id: string) => {
        const uuid = uuids[id];
        console.log(`Getting UUID for ID ${id}: ${uuid || 'not found'}`);
        return uuid;
    };
    
    return { uuids, setUUID, getUUID };
};