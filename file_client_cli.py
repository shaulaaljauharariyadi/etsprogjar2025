import socket
import json
import base64
import logging
import os
import time
import concurrent.futures

server_address = ('127.0.0.1', 12345)  # Ganti sesuai servermu

def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(15)  # Add a timeout for the whole operation
    try:
        sock.connect(server_address)
        sock.sendall((command_str + "\r\n\r\n").encode())
        data_received = ""
        while True:
            try:
                data = sock.recv(4096)
            except socket.timeout:
                print("Timeout while waiting for server response.")
                return False
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break
        hasil = json.loads(data_received)
        return hasil
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        sock.close()

def remote_list():
    command_str = f"LIST"
    hasil = send_command(command_str)
    if hasil and hasil['status'] == 'OK':
        return hasil['data']
    else:
        return False

def remote_get(filename=""):
    command_str = f"GET {filename}"
    hasil = send_command(command_str)
    if hasil and hasil['status'] == 'OK':
        namafile = hasil['data_namafile']
        isifile = base64.b64decode(hasil['data_file'])
        os.makedirs('files', exist_ok=True)
        with open(os.path.join('files',namafile), 'wb+') as fp:
            fp.write(isifile)
        return True
    else:
        print("Gagal")
        return False

def remote_upload(filepath=""):
    try:
        with open(filepath, 'rb') as f:
            content_b64 = base64.b64encode(f.read()).decode()
        filename = os.path.basename(filepath)
        command_str = f'UPLOAD filename={filename} content={content_b64}'
        hasil = send_command(command_str)
        if hasil and hasil['status'] == 'OK':
            return True
        else:
            return False
    except Exception as e:
        print(f"Gagal upload: {str(e)}")
        return False

# Fungsi worker untuk stress test
def worker_upload(filepath):
    start = time.time()
    success = remote_upload(filepath)
    durasi = time.time() - start
    ukuran = os.path.getsize(filepath) if success else 0
    return success, durasi, ukuran

def worker_download(filename):
    start = time.time()
    success = remote_get(filename)
    durasi = time.time() - start
    ukuran = os.path.getsize(filename) if success and os.path.exists(filename) else 0
    return success, durasi, ukuran

def worker_list():
    start = time.time()
    data = remote_list()
    durasi = time.time() - start
    success = data is not False
    return success, durasi, 0

# Fungsi stress test
def stress_test(op, file_target, n_workers, pool_type='thread'):
    results = []
    if pool_type == 'thread':
        Executor = concurrent.futures.ThreadPoolExecutor
    else:
        Executor = concurrent.futures.ProcessPoolExecutor

    with Executor(max_workers=n_workers) as executor:
        if op == 'upload':
            futures = [executor.submit(worker_upload, file_target) for _ in range(n_workers)]
        elif op == 'download':
            futures = [executor.submit(worker_download, file_target) for _ in range(n_workers)]
        elif op == 'list':
            futures = [executor.submit(worker_list) for _ in range(n_workers)]
        else:
            raise Exception("Operasi tidak dikenali")

        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())
    return results

def rekap_hasil(results, op):
    sukses = sum(1 for x in results if x[0])
    gagal = len(results) - sukses
    total_time = sum(x[1] for x in results)
    total_bytes = sum(x[2] for x in results)
    throughput = (total_bytes / total_time) if total_time > 0 else 0
    print(f"Operasi: {op}")
    print(f"Jumlah worker: {len(results)}")
    print(f"Sukses: {sukses}, Gagal: {gagal}")
    print(f"Total waktu: {total_time:.2f} detik")
    print(f"Total bytes: {total_bytes}")
    print(f"Throughput: {throughput:.2f} bytes/detik")
    print("="*30)

if __name__ == '__main__':
    # Contoh konfigurasi
    operasi = 'download'
    file_target = 'files/100mbexample-jpg.jpg'  # Nama file yang sudah ada di server
    n_workers = 10
    pool_type = 'thread'  # 'thread' atau 'process'
    # Untuk download, pastikan file_target adalah nama file yang sudah ada di server
    # Untuk upload, file_target adalah path file lokal yang akan diupload

    results = stress_test(operasi, file_target, n_workers, pool_type)
    rekap_hasil(results, operasi)