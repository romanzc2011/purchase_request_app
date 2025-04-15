import { useQuery, useQueryClient } from "@tanstack/react-query";

const STORAGE_KEY = 'uuid_store';

export const useUUIDStore = () => {
    const queryClient = useQueryClient();
    
    // Get UUIDs from localStorage or query cache
    const { data: uuids = {} } = useQuery<Record<string, string>>({
        queryKey: ['uuids'],
        queryFn: () => {
            // Try to get from localStorage first
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored) {
                try {
                    return JSON.parse(stored);
                } catch (e) {
                    console.error('Error parsing stored UUIDs:', e);
                }
            }
            return {};
        },
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
            // Persist to localStorage
            localStorage.setItem(STORAGE_KEY, JSON.stringify(newData));
            console.log("Updated UUID store:", newData);
            return newData;
        });
    };
    
    // Get a UUID for a specific ID
    const getUUID = async (id: string) => {
        // Try localStorage first
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            try {
                const storedData = JSON.parse(stored);
                if (storedData[id]) {
                    console.log(`Getting UUID for ID ${id} from localStorage: ${storedData[id]}`);
                    return storedData[id];
                }
            } catch (e) {
                console.error('Error parsing stored UUIDs:', e);
            }
        }
        
        // Try query cache
        const uuid = uuids[id];
        if (uuid) {
            console.log(`Getting UUID for ID ${id} from cache: ${uuid}`);
            return uuid;
        }
        
        // If not found in cache or localStorage, try to fetch from backend
        console.log(`UUID not found in cache for ID ${id}, trying backend...`);
        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL}/api/getUUID/${id}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                },
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.uuid) {
                    console.log(`Got UUID from backend for ID ${id}: ${data.uuid}`);
                    // Store in cache and localStorage for future use
                    setUUID(id, data.uuid);
                    return data.uuid;
                }
            }
            
            console.log(`No UUID found in backend for ID ${id}`);
            return null;
        } catch (error) {
            console.error(`Error fetching UUID from backend for ID ${id}:`, error);
            return null;
        }
    };
    
    return { uuids, setUUID, getUUID };
};