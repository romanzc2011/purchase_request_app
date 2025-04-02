from multiprocessing import shared_memory

class IPC_Service:
    def __init__(self):
        self.SHM_SIZE = 1024
        self.msg = "REFRESH_INDEX"
        try:
            self.shm = shared_memory.SharedMemory(name="refresh_index")
        except FileNotFoundError:
            self.shm = shared_memory.SharedMemory(create=True, size=self.SHM_SIZE, name="refresh_index")
            
    def send_to_shm(self):
        data = self.msg.encode('utf-8')
        self.shm.buf[:len(data)] = data
        
    def receive_from_shm(self):
        shm = shared_memory.SharedMemory(name="refresh_index")
        # Read buffer and strip traailing zeros
        received_data = bytes(shm.buf[:self.SHM_SIZE]).rstrip(b'\x00')
        shm.close()
        return received_data
  
ipc_instance = IPC_Service()
        