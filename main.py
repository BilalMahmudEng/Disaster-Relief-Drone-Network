from multiprocessing import Process
import runpy
import time

def run_server():
    runpy.run_path("Server.py")

def run_client():
    runpy.run_path("Client.py")

if __name__ == "__main__":
    server_proc = Process(target=run_server)
    server_proc.start()

    time.sleep(1)

    # Start client
    client_proc = Process(target=run_client)
    client_proc.start()
