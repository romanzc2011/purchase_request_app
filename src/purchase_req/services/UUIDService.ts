import { useQuery, useQueryClient } from "@tanstack/react-query";

const STORAGE_KEY = 'UUID_store';

export const useUUIDStore = () => {
    const queryClient = useQueryClient();
    
    // Get UUIDs from localStorage or query cache
    const { data: UUIDs = {} } = useQuery<Record<string, string>>({
        queryKey: ['UUIDs'],
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
    const setUUID = (ID: string, UUID: string) => {
        console.log(`Setting UUID for ID ${ID}: ${UUID}`);
        queryClient.setQueryData(['UUIDs'], (oldData: Record<string, string> = {}) => {
            const newData = {
                ...oldData,
                [ID]: UUID
            };
            // Persist to localStorage
            localStorage.setItem(STORAGE_KEY, JSON.stringify(newData));
            console.log("Updated UUID store:", newData);
            return newData;
        });
    };
    
    // Get a UUID for a specific ID
    const getUUID = async (ID: string) => {
        // Try localStorage first
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            try {
                const storedData = JSON.parse(stored);
                if (storedData[ID]) {
                    return storedData[ID];
                }
            } catch (e) {
                console.error('Error parsing stored UUIDs:', e);
            }
        }
        
        // Try query cache
        const UUID = UUIDs[ID];
        if (UUID) {
            console.log(`Getting UUID for ID ${ID} from cache: ${UUID}`);
            return UUID;
        }
        
        // If not found in cache or localStorage, try to fetch from backend
        console.log(`UUID not found in cache for ID ${ID}, trying backend...`);
        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL}/api/getUUID/${ID}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                },
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.UUID) {
                    console.log(`Got UUID from backend for ID ${ID}: ${data.UUID}`);
                    // Store in cache and localStorage for future use
                    setUUID(ID, data.UUID);
                    return data.UUID;
                }
            }
            
            console.log(`No UUID found in backend for ID ${ID}`);
            return null;
        } catch (error) {
            console.error(`Error fetching UUID from backend for ID ${ID}:`, error);
            return null;
        }
    };

    // Clear all cached UUIDs
    const clearCache = () => {
        console.log('Clearing UUID cache...');
        localStorage.removeItem(STORAGE_KEY);
        queryClient.setQueryData(['UUIDs'], {});
        console.log('UUID cache cleared');
    };

    return { UUIDs, setUUID, getUUID, clearCache };
};