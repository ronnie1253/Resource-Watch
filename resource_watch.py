import psutil
import time
import os
import json
import platform
import matplotlib.pyplot as plt

if platform.system() == 'Windows':
    import win32gui
    import win32process

# Global variables for tracking usage data on the system .
usage_data = {}
total_system_usage = 0

def get_active_window_name():
    if platform.system() == 'Windows':
        try:
            window = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(window)
            if pid <= 0:
                return None
            return psutil.Process(pid).name()
        except Exception as e:
            print(f"Error retrieving active window name: {e}")
            return None
    else:
        # This code is works only for windows , so for any other OS provide the implementation here
        return None

def get_process_memory_usage(pid):
    try:
        proc = psutil.Process(pid)
        memory_info = proc.memory_info()
        return memory_info.rss  # Resident Set Size (RAM)
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
        print(f"Error retrieving memory usage for PID {pid}: {e}")
        return 0

def get_process_disk_usage(pid):
    try:
        proc = psutil.Process(pid)
        io_counters = proc.io_counters()
        return io_counters.read_bytes + io_counters.write_bytes  # Disk I/O
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
        print(f"Error retrieving disk usage for PID {pid}: {e}")
        return 0

def track_application_usage(usage_data):
    active_window_name = get_active_window_name()
    if not active_window_name:
        return

    current_time = time.time()
    pid = psutil.Process().pid  # Changed to use current process ID

    try:
        if active_window_name in usage_data:
            usage_data[active_window_name]['time_spent'] += 1
            if 'ram_usage' in usage_data[active_window_name]:
                usage_data[active_window_name]['ram_usage'] += get_process_memory_usage(pid)
            else:
                usage_data[active_window_name]['ram_usage'] = get_process_memory_usage(pid)
                
            if 'disk_usage' in usage_data[active_window_name]:
                usage_data[active_window_name]['disk_usage'] += get_process_disk_usage(pid)
            else:
                usage_data[active_window_name]['disk_usage'] = get_process_disk_usage(pid)
        else:
            # Initialize the new application entry
            usage_data[active_window_name] = {
                'time_spent': 1,
                'ram_usage': get_process_memory_usage(pid),
                'disk_usage': get_process_disk_usage(pid)
            }
    except KeyError:
        usage_data[active_window_name] = {
            'time_spent': 1,
            'ram_usage': get_process_memory_usage(pid),
            'disk_usage': get_process_disk_usage(pid)
        }

    usage_data['total_system_usage'] += 1

def save_usage_data(file_path, usage_data):
    with open(file_path, 'w') as f:
        json.dump(usage_data, f)

def load_usage_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {'total_system_usage': 0}

def plot_usage_data(usage_data):
    apps = list(usage_data.keys())
    app_names = [app for app in apps if app != 'total_system_usage']
    
    usage_times = [usage_data[app]['time_spent'] for app in app_names]
    ram_usages = [usage_data[app].get('ram_usage', 0) / (1024 * 1024) for app in app_names]  # Convert to MB
    disk_usages = [usage_data[app].get('disk_usage', 0) / (1024 * 1024) for app in app_names]  # Convert to MB

    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    
    ax1.bar(app_names, usage_times, color='b', alpha=0.5, label='Usage Time (s)')
    ax2.plot(app_names, ram_usages, color='r', marker='o', label='RAM Usage (MB)')
    ax2.plot(app_names, disk_usages, color='g', marker='s', label='Disk Usage (MB)')
    
    ax1.set_xlabel('Application')
    ax1.set_ylabel('Usage Time (seconds)')
    ax2.set_ylabel('Usage (MB)')
    ax1.set_title('Application Usage Statistics')
    
    ax1.set_xticks(range(len(app_names)))
    ax1.set_xticklabels(app_names, rotation=45, ha='right')
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')

    plt.tight_layout()
    plt.show()

def main():
    global usage_data, total_system_usage
    usage_file = 'usage_data.json'
    usage_data = load_usage_data(usage_file)

    if 'total_system_usage' not in usage_data:
        usage_data['total_system_usage'] = 0

    try:
        while True:
            track_application_usage(usage_data)
            time.sleep(1)
            if int(time.time()) % 60 == 0:  # Aggregate and plot every minute
                save_usage_data(usage_file, usage_data)
                plot_usage_data(usage_data)
    except KeyboardInterrupt:
        save_usage_data(usage_file, usage_data)
        print("\nExiting and saving usage data...")

if __name__ == '__main__':
    main()
