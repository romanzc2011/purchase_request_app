from multiprocessing import shared_memory

class IPC_Service:
    def __init__(self):
        self.SHM_SIZE = 1024
        self.msg = None
        try:
            self.shm = shared_memory.SharedMemory(name="status")
        except FileNotFoundError:
            self.shm = shared_memory.SharedMemory(create=True, size=self.SHM_SIZE, name="status")
            
    def send_to_shm(self, msg):
        self.set_msg(msg)
        msg = self.get_msg()
        
        data = msg.encode('utf-8')
        self.shm.buf[:len(data)] = data
        
    def receive_from_shm(self):
        shm = shared_memory.SharedMemory(name="status")
        # Read buffer and strip traailing zeros
        received_data = bytes(shm.buf[:self.SHM_SIZE]).rstrip(b'\x00')
        shm.close()
        return received_data
    
    def set_msg(self, msg):
        self.msg = msg
    
    def get_msg(self):
        return self.msg
  
ipc_instance = IPC_Service()
        