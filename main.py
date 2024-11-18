import sys
import os
import psutil
import platform
import logging
import ctypes
import win32com.shell.shell as shell
import win32con
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    try:
        if sys.argv[-1] != 'asadmin':
            script = os.path.abspath(sys.argv[0])
            params = ' '.join([script] + sys.argv[1:] + ['asadmin'])
            shell.ShellExecuteEx(lpVerb='runas',
                               lpFile=sys.executable,
                               lpParameters=params,
                               nShow=win32con.SW_SHOW)
            sys.exit()
    except Exception as e:
        print(f"Error requesting admin rights: {e}")
        logging.error(f"Admin elevation error: {e}")
        QMessageBox.critical(None, "Error", 
                           "Failed to get administrative privileges. The application may not work correctly.\n"
                           f"Error: {str(e)}")

class SingleApplication(QApplication):
    messageReceived = pyqtSignal(str)

    def __init__(self, argv):
        super().__init__(argv)
        self._socketServer = None
        self._socketName = 'AiSystemOptimizerSocket'
        self._sharedMemory = QSharedMemory('AiSystemOptimizerMemory')
        
        # Try to create shared memory
        if not self._sharedMemory.create(1):
            # Another instance exists
            socket = QLocalSocket()
            socket.connectToServer(self._socketName)
            if socket.waitForConnected(500):
                # Send a message to the existing instance
                socket.write(b'ACTIVATE')
                socket.waitForBytesWritten()
                socket.disconnectFromServer()
                sys.exit(0)
            else:
                # Clean up any stale shared memory
                self._sharedMemory.attach()
                self._sharedMemory.detach()
                if not self._sharedMemory.create(1):
                    logging.error("Failed to create shared memory")
                    sys.exit(1)
        
        # Set up server for receiving messages
        self._socketServer = QLocalServer()
        if not self._socketServer.listen(self._socketName):
            self._socketServer.removeServer(self._socketName)
            self._socketServer.listen(self._socketName)
        self._socketServer.newConnection.connect(self._handleMessage)

    def _handleMessage(self):
        socket = self._socketServer.nextPendingConnection()
        if socket.waitForReadyRead(1000):
            self.messageReceived.emit(str(socket.readAll(), 'utf-8'))

class SystemScanner(QThread):
    scan_complete = pyqtSignal(dict)
    scan_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.mutex = QMutex()
        # Initialize COM in the main thread
        self.coinit_done = False
        try:
            pythoncom.CoInitialize()
            self.coinit_done = True
        except:
            pass

    def __del__(self):
        if self.coinit_done:
            pythoncom.CoUninitialize()

    def get_cpu_info(self):
        try:
            cpu_info = {}
            # Get CPU name from WMI
            import wmi
            w = wmi.WMI()
            for processor in w.Win32_Processor():
                cpu_info['name'] = processor.Name
                break
            
            # Get CPU cores and usage from psutil
            cpu_info['cores'] = psutil.cpu_count(logical=False)
            cpu_info['threads'] = psutil.cpu_count(logical=True)
            cpu_info['usage'] = psutil.cpu_percent(interval=1)
            
            return (f"Name: {cpu_info['name']}\n"
                   f"Physical cores: {cpu_info['cores']}\n"
                   f"Logical processors: {cpu_info['threads']}\n"
                   f"Current Usage: {cpu_info['usage']}%")
        except Exception as e:
            logging.error(f"Error getting CPU info: {str(e)}")
            return f"Error retrieving CPU info: {str(e)}"

    def get_memory_info(self):
        try:
            memory = psutil.virtual_memory()
            total_gb = memory.total / (1024 ** 3)
            used_gb = memory.used / (1024 ** 3)
            free_gb = memory.free / (1024 ** 3)
            percent_used = memory.percent
            
            return (f"Total: {total_gb:.1f} GB\n"
                   f"Used: {used_gb:.1f} GB\n"
                   f"Free: {free_gb:.1f} GB\n"
                   f"Usage: {percent_used}%")
        except Exception as e:
            logging.error(f"Error getting memory info: {str(e)}")
            return f"Error retrieving memory info: {str(e)}"

    def get_gpu_info(self):
        try:
            import wmi
            w = wmi.WMI()
            gpu_info = []
            
            for gpu in w.Win32_VideoController():
                name = gpu.Name
                memory = getattr(gpu, 'AdapterRAM', 0)
                if memory:
                    memory_gb = memory / (1024 ** 3)
                    gpu_info.append(f"{name} ({memory_gb:.1f} GB)")
                else:
                    gpu_info.append(name)
            
            return "\n".join(gpu_info) if gpu_info else "No GPU information available"
        except Exception as e:
            logging.error(f"Error getting GPU info: {str(e)}")
            return f"Error retrieving GPU info: {str(e)}"

    def get_storage_info(self):
        try:
            storage_info = []
            for partition in psutil.disk_partitions():
                if partition.fstype:  # Skip empty drives
                    usage = psutil.disk_usage(partition.mountpoint)
                    total_gb = usage.total / (1024 ** 3)
                    used_gb = usage.used / (1024 ** 3)
                    free_gb = usage.free / (1024 ** 3)
                    percent_used = usage.percent
                    
                    storage_info.append(
                        f"Drive {partition.device}\n"
                        f"Total: {total_gb:.1f} GB\n"
                        f"Used: {used_gb:.1f} GB\n"
                        f"Free: {free_gb:.1f} GB\n"
                        f"Usage: {percent_used}%\n"
                    )
            
            return "\n".join(storage_info) if storage_info else "No storage information available"
        except Exception as e:
            logging.error(f"Error getting storage info: {str(e)}")
            return f"Error retrieving storage info: {str(e)}"

    def get_background_processes(self):
        background_apps = {
            # Gaming platforms
            'steam.exe': 'Steam Gaming Platform',
            'epicgameslauncher.exe': 'Epic Games Launcher',
            'goggalaxy.exe': 'GOG Galaxy',
            'origin.exe': 'Origin',
            'battlenet.exe': 'Battle.net',
            
            # Update services
            'adobearm.exe': 'Adobe Acrobat Update Service',
            'armsvc.exe': 'Adobe Acrobat Update Service',
            'adobeupdateservice.exe': 'Adobe Update Service',
            'ccxprocess.exe': 'Adobe Creative Cloud',
            'adobe_updater.exe': 'Adobe Updater',
            
            # Browser-related
            'chrome.exe': 'Google Chrome',
            'firefox.exe': 'Mozilla Firefox',
            'msedge.exe': 'Microsoft Edge',
            
            # Common background services
            'onedrive.exe': 'Microsoft OneDrive',
            'dropbox.exe': 'Dropbox',
            'googledrivesync.exe': 'Google Drive',
            'skype.exe': 'Skype',
            'teams.exe': 'Microsoft Teams',
            'discord.exe': 'Discord',
            
            # Hardware control panels
            'lcbuttond.exe': 'Lenovo Controller',
            'asustploader.exe': 'ASUS Smart Gesture',
            'igfxem.exe': 'Intel Graphics',
            'rundll32.exe': 'Windows Runtime DLL',
            
            # Other common resource-intensive apps
            'wallpaperengine.exe': 'Wallpaper Engine',
            'spotify.exe': 'Spotify',
            'nahimic3.exe': 'Nahimic Audio',
        }
        
        running_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                proc_name = proc.info['name'].lower()
                
                # Check if this is a known background process
                if proc_name in background_apps:
                    process_info = {
                        'name': background_apps[proc_name],
                        'exe_name': proc_name,
                        'pid': proc.info['pid'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_percent': proc.info['memory_percent']
                    }
                    running_processes.append(process_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        return running_processes

    def optimize_background_processes(self):
        processes = self.get_background_processes()
        optimization_results = []
        
        total_cpu_saved = 0
        total_memory_saved = 0
        
        for proc in processes:
            if proc['cpu_percent'] > 0.5 or proc['memory_percent'] > 0.5:
                try:
                    # Instead of killing, we'll just report
                    cpu_impact = proc['cpu_percent']
                    memory_impact = proc['memory_percent']
                    
                    recommendation = {
                        'name': proc['name'],
                        'exe_name': proc['exe_name'],
                        'cpu_impact': cpu_impact,
                        'memory_impact': memory_impact,
                        'recommendation': 'Consider closing or disabling at startup'
                    }
                    
                    total_cpu_saved += cpu_impact
                    total_memory_saved += memory_impact
                    
                    optimization_results.append(recommendation)
                except Exception as e:
                    logging.error(f"Error processing {proc['name']}: {str(e)}")
        
        return optimization_results, total_cpu_saved, total_memory_saved

    def run(self):
        try:
            if not self.mutex.tryLock():
                self.scan_error.emit("A scan is already in progress")
                return

            logging.info("Starting system scan")
            
            # Gather system information using direct Windows API calls
            system_info = {}
            
            # Get CPU information
            system_info['cpu'] = self.get_cpu_info()
            if "Error retrieving CPU info" in system_info['cpu']:
                logging.warning("CPU info retrieval failed, but continuing with scan")
            
            # Get memory information
            system_info['memory'] = self.get_memory_info()
            
            # Get GPU information
            system_info['gpu'] = self.get_gpu_info()
            
            # Get storage information
            system_info['storage'] = self.get_storage_info()
            
            # Get background processes
            system_info['background_processes'] = self.get_background_processes()
            
            self.scan_complete.emit(system_info)
            logging.info("System scan completed successfully")
            
        except Exception as e:
            error_msg = f"Error during system scan: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            self.scan_error.emit(error_msg)
        finally:
            if self.mutex.tryLock():
                self.mutex.unlock()
            self.mutex.unlock()

class OptimizationWorker(QThread):
    optimization_complete = pyqtSignal(dict)
    progress_update = pyqtSignal(str)
    optimization_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.mutex = QMutex()
        # Create startupinfo to hide console windows
        self.startupinfo = subprocess.STARTUPINFO()
        self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        self.startupinfo.wShowWindow = subprocess.SW_HIDE

    def optimize_power_settings(self):
        try:
            self.progress_update.emit("Optimizing power settings...")
            # Set power plan to high performance
            subprocess.run(['powercfg', '/setactive', '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'], 
                         startupinfo=self.startupinfo, check=True)
            return True
        except Exception as e:
            logging.error(f"Error optimizing power settings: {str(e)}")
            return False

    def optimize_system_services(self):
        try:
            self.progress_update.emit("Optimizing system services...")
            # List of services that can be safely disabled for AI workloads
            services_to_optimize = [
                'SysMain', # Superfetch
                'DiagTrack', # Connected User Experiences and Telemetry
                'WSearch'  # Windows Search
            ]
            
            for service in services_to_optimize:
                try:
                    # Stop and disable the service
                    subprocess.run(['sc', 'stop', service], 
                                 startupinfo=self.startupinfo, check=False)
                    subprocess.run(['sc', 'config', service, 'start=disabled'], 
                                 startupinfo=self.startupinfo, check=False)
                except Exception as service_error:
                    logging.warning(f"Could not optimize service {service}: {str(service_error)}")
            return True
        except Exception as e:
            logging.error(f"Error optimizing services: {str(e)}")
            return False

    def optimize_memory(self):
        try:
            self.progress_update.emit("Optimizing memory settings...")
            # Set virtual memory (page file) to system managed
            subprocess.run(['wmic', 'computersystem', 'where', 'name="%computername%"', 
                          'set', 'AutomaticManagedPagefile=True'], 
                         startupinfo=self.startupinfo, check=False)
            return True
        except Exception as e:
            logging.error(f"Error optimizing memory: {str(e)}")
            return False

    def optimize_process_priority(self):
        try:
            self.progress_update.emit("Optimizing process priorities...")
            # Get the current process
            current_process = psutil.Process()
            
            # Set high priority for the current process
            current_process.nice(psutil.HIGH_PRIORITY_CLASS)
            
            # Lower priority of non-essential processes
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    if proc.pid != current_process.pid and proc.name().lower() not in ['system', 'idle']:
                        proc_handle = psutil.Process(proc.pid)
                        if proc_handle.nice() > psutil.NORMAL_PRIORITY_CLASS:
                            proc_handle.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            return True
        except Exception as e:
            logging.error(f"Error optimizing process priorities: {str(e)}")
            return False

    def run(self):
        try:
            if not self.mutex.tryLock():
                self.optimization_error.emit("Optimization is already in progress")
                return

            logging.info("Starting system optimization")
            optimization_results = {
                'power': False,
                'services': False,
                'memory': False,
                'process_priority': False
            }
            
            # Run optimizations
            optimization_results['power'] = self.optimize_power_settings()
            optimization_results['services'] = self.optimize_system_services()
            optimization_results['memory'] = self.optimize_memory()
            optimization_results['process_priority'] = self.optimize_process_priority()
            
            # Calculate success percentage
            success_count = sum(1 for result in optimization_results.values() if result)
            total_optimizations = len(optimization_results)
            optimization_results['success_percentage'] = (success_count / total_optimizations) * 100
            
            self.optimization_complete.emit(optimization_results)
            logging.info("System optimization completed")
            
        except Exception as e:
            error_msg = f"Error during optimization: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            self.optimization_error.emit(error_msg)
        finally:
            if self.mutex.tryLock():
                self.mutex.unlock()
            self.mutex.unlock()

class OptimizationDialog(QDialog):
    def __init__(self, processes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Optimization Options")
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)

        # Add description
        description = QLabel("Select programs to optimize:")
        description.setWordWrap(True)
        layout.addWidget(description)

        # Create scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Group processes by category
        self.checkboxes = []
        
        # Gaming platforms
        if any(p for p in processes if p['category'] == 'gaming'):
            gaming_group = QGroupBox("Gaming Applications")
            gaming_layout = QVBoxLayout()
            for proc in processes:
                if proc['category'] == 'gaming':
                    cb = QCheckBox(f"{proc['name']} (CPU: {proc['cpu']:.1f}%, Memory: {proc['memory']:.1f}%)")
                    cb.setChecked(True)
                    cb.process = proc
                    gaming_layout.addWidget(cb)
                    self.checkboxes.append(cb)
            gaming_group.setLayout(gaming_layout)
            scroll_layout.addWidget(gaming_group)

        # Communication apps
        if any(p for p in processes if p['category'] == 'communication'):
            comm_group = QGroupBox("Communication Apps")
            comm_layout = QVBoxLayout()
            for proc in processes:
                if proc['category'] == 'communication':
                    cb = QCheckBox(f"{proc['name']} (CPU: {proc['cpu']:.1f}%, Memory: {proc['memory']:.1f}%)")
                    cb.setChecked(True)
                    cb.process = proc
                    comm_layout.addWidget(cb)
                    self.checkboxes.append(cb)
            comm_group.setLayout(comm_layout)
            scroll_layout.addWidget(comm_group)

        # Background services
        if any(p for p in processes if p['category'] == 'background'):
            background_group = QGroupBox("Background Services")
            background_layout = QVBoxLayout()
            for proc in processes:
                if proc['category'] == 'background':
                    cb = QCheckBox(f"{proc['name']} (CPU: {proc['cpu']:.1f}%, Memory: {proc['memory']:.1f}%)")
                    cb.setChecked(True)
                    cb.process = proc
                    background_layout.addWidget(cb)
                    self.checkboxes.append(cb)
            background_group.setLayout(background_layout)
            scroll_layout.addWidget(background_group)

        # Other resource-intensive processes
        if any(p for p in processes if p['category'] == 'other'):
            other_group = QGroupBox("Other Resource-Intensive Programs")
            other_layout = QVBoxLayout()
            for proc in processes:
                if proc['category'] == 'other':
                    cb = QCheckBox(f"{proc['name']} (CPU: {proc['cpu']:.1f}%, Memory: {proc['memory']:.1f}%)")
                    cb.setChecked(True)
                    cb.process = proc
                    other_layout.addWidget(cb)
                    self.checkboxes.append(cb)
            other_group.setLayout(other_layout)
            scroll_layout.addWidget(other_group)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Add optimization options
        options_group = QGroupBox("Optimization Options")
        options_layout = QVBoxLayout()
        
        self.startup_cb = QCheckBox("Disable selected programs from starting with Windows")
        self.startup_cb.setChecked(True)
        options_layout.addWidget(self.startup_cb)
        
        self.terminate_cb = QCheckBox("Close selected programs now")
        self.terminate_cb.setChecked(True)
        options_layout.addWidget(self.terminate_cb)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Add buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_selected_processes(self):
        return [cb.process for cb in self.checkboxes if cb.isChecked()]

    def get_options(self):
        return {
            'disable_startup': self.startup_cb.isChecked(),
            'terminate_now': self.terminate_cb.isChecked()
        }

class ProcessScannerThread(QThread):
    finished = pyqtSignal(list)
    progress = pyqtSignal(str)
    
    def run(self):
        try:
            self.progress.emit("Initializing process scan...")
            processes = []
            
            # Process scanning in smaller batches
            try:
                # Get process list without CPU info first
                self.progress.emit("Getting process list...")
                all_processes = list(psutil.process_iter(['pid', 'name']))
                
                # Initialize CPU monitoring
                psutil.cpu_percent(interval=0.1)
                
                # Process in batches of 10
                batch_size = 10
                for i in range(0, len(all_processes), batch_size):
                    batch = all_processes[i:i+batch_size]
                    self.progress.emit(f"Analyzing processes... ({i}/{len(all_processes)})")
                    
                    for proc in batch:
                        try:
                            with proc.oneshot():  # More efficient resource usage
                                name = proc.name().lower()
                                cpu = proc.cpu_percent() or 0
                                mem = proc.memory_percent() or 0
                                
                                # Only include processes using significant resources
                                if cpu > 0.1 or mem > 0.1:
                                    category = 'other'
                                    if any(g in name for g in ['steam', 'epic', 'game', 'origin', 'battle.net']):
                                        category = 'gaming'
                                    elif any(c in name for c in ['discord', 'slack', 'teams', 'whatsapp', 'telegram']):
                                        category = 'communication'
                                    elif any(b in name for b in ['update', 'service', 'agent', 'helper']):
                                        category = 'background'
                                        
                                    processes.append({
                                        'name': proc.name(),
                                        'pid': proc.pid,
                                        'cpu': cpu,
                                        'memory': mem,
                                        'category': category
                                    })
                        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception) as e:
                            continue
                            
                    # Let the UI breathe between batches
                    QThread.msleep(10)
                
            except Exception as e:
                logging.error(f"Error during process scanning: {e}")
            
            # Sort processes by resource usage
            self.progress.emit("Finalizing results...")
            processes.sort(key=lambda x: x['cpu'] + x['memory'], reverse=True)
            self.finished.emit(processes)
            
        except Exception as e:
            logging.error(f"Error in process scanner: {e}")
            self.finished.emit([])

class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Loading")
        self.setFixedSize(300, 100)
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        
        layout = QVBoxLayout(self)
        
        # Add spinning progress bar
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 0)  # Makes it spin
        layout.addWidget(self.progress)
        
        # Add status label
        self.status = QLabel("Initializing...", self)
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status)
    
    def update_status(self, message):
        self.status.setText(message)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI System Optimizer")
        self.setMinimumSize(800, 600)
        
        # Show warning message box
        QMessageBox.warning(
            self,
            "Important Notice",
            "During system scanning, command windows may briefly appear.\nThis is normal and part of the scanning process.",
            QMessageBox.StandardButton.Ok
        )
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Add warning label at the top
        warning_label = QLabel("⚠️ WARNING: Command windows will appear during scanning")
        warning_label.setStyleSheet("""
            QLabel {
                color: #721c24;
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                padding: 15px;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        layout.addWidget(warning_label)
        
        # Create buttons
        button_layout = QHBoxLayout()
        self.scan_button = QPushButton("Scan System")
        self.optimize_button = QPushButton("Optimize for AI")
        
        # Style buttons
        button_style = """
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 15px;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """
        self.scan_button.setStyleSheet(button_style)
        self.optimize_button.setStyleSheet(button_style.replace('#007bff', '#28a745').replace('#0056b3', '#218838'))
        
        # Connect buttons
        self.scan_button.clicked.connect(self.start_scan)
        self.optimize_button.clicked.connect(self.optimize_system)
        
        button_layout.addWidget(self.scan_button)
        button_layout.addWidget(self.optimize_button)
        layout.addLayout(button_layout)
        
        # Create status label
        self.status_label = QLabel("Click 'Scan System' to begin")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #0c5460;
                background-color: #d1ecf1;
                border: 1px solid #bee5eb;
                padding: 15px;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Create progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #007bff;
                border-radius: 4px;
                text-align: center;
                padding: 2px;
            }
            QProgressBar::chunk {
                background-color: #007bff;
            }
        """)
        layout.addWidget(self.progress)
        
        # Create scroll area for system info
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        # Create widget for scroll area
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Create system info labels
        self.cpu_info = QLabel("CPU Information will appear here")
        self.memory_info = QLabel("Memory Information will appear here")
        self.gpu_info = QLabel("GPU Information will appear here")
        self.storage_info = QLabel("Storage Information will appear here")
        self.optimization_info = QLabel("")
        
        # Style all info labels
        info_style = """
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 15px;
                border-radius: 4px;
                font-size: 14px;
            }
        """
        for label in [self.cpu_info, self.memory_info, self.gpu_info, self.storage_info, self.optimization_info]:
            label.setStyleSheet(info_style)
            label.setWordWrap(True)
            scroll_layout.addWidget(label)
            scroll_layout.addSpacing(10)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        error_msg = f"An unexpected error occurred: {str(exc_value)}"
        self.handle_scan_error(error_msg)
    
    def start_scan(self):
        """Start the system scanning process."""
        self.scan_button.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.status_label.setText("Scanning system... Note: Command windows may briefly appear during scanning - this is normal.")
        
        # Start the scanner in a new thread
        self.scanner = SystemScanner()
        self.scanner.scan_complete.connect(self.handle_scan_complete)
        self.scanner.scan_error.connect(self.handle_scan_error)
        self.scanner.start()
    
    def handle_scan_error(self, error_message):
        logging.error(f"Scan error: {error_message}")
        self.status_label.setText(error_message)
        self.scan_button.setEnabled(True)
        self.progress.setVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
    
    def update_status(self, message):
        logging.debug(f"Status update: {message}")
        self.status_label.setText(message)
        QApplication.processEvents()

    def format_bytes(self, bytes):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024
    
    def handle_scan_complete(self, system_info):
        try:
            # Update CPU info
            self.cpu_info.setText(system_info['cpu'])

            # Update Memory info
            self.memory_info.setText(system_info['memory'])

            # Update GPU info
            self.gpu_info.setText(system_info['gpu'])

            # Update Storage info
            self.storage_info.setText(system_info['storage'])

            # Store background process info for optimization
            if 'background_processes' in system_info:
                self.background_processes = system_info['background_processes']

            # Enable optimize button after scan
            self.status_label.setText("System scan complete! Click 'Optimize for AI' for recommendations.")
            self.progress.setValue(100)
            self.scan_button.setEnabled(True)

        except Exception as e:
            self.handle_exception(type(e), e, e.__traceback__)

    def optimize_system(self):
        try:
            # Show loading dialog
            self.loading = LoadingDialog(self)
            
            # Create and start process scanner thread
            self.scanner_thread = ProcessScannerThread()
            self.scanner_thread.finished.connect(self.on_scanner_finished)
            self.scanner_thread.progress.connect(self.loading.update_status)
            
            # Show dialog after connecting signals
            self.loading.show()
            
            # Start scanning in thread
            self.scanner_thread.start()
            
        except Exception as e:
            error_msg = f"Error during optimization: {str(e)}"
            logging.error(error_msg)
            self.optimization_info.setText(error_msg)
            self.status_label.setText("Error during optimization!")
            if hasattr(self, 'loading'):
                self.loading.close()

    def on_scanner_finished(self, processes):
        try:
            # Close loading dialog
            if hasattr(self, 'loading'):
                self.loading.close()
            
            if processes:
                # Show optimization dialog
                dialog = OptimizationDialog(processes, self)
                if dialog.exec():
                    selected_processes = dialog.get_selected_processes()
                    options = dialog.get_options()
                    
                    optimization_text = "Optimization Results\n"
                    optimization_text += "=" * 50 + "\n\n"
                    
                    if selected_processes:
                        # Get our own process ID to prevent self-termination
                        our_pid = os.getpid()
                        
                        if options['disable_startup']:
                            optimization_text += "Disabling programs from startup:\n"
                            import winreg
                            try:
                                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                                   r"Software\Microsoft\Windows\CurrentVersion\Run", 
                                                   0, winreg.KEY_ALL_ACCESS)
                                for proc in selected_processes:
                                    try:
                                        winreg.DeleteValue(key, proc['name'])
                                        optimization_text += f"✓ Disabled {proc['name']} from startup\n"
                                    except WindowsError:
                                        pass
                                winreg.CloseKey(key)
                            except Exception as e:
                                optimization_text += f"! Error modifying startup programs: {e}\n"
                            optimization_text += "\n"
                        
                        if options['terminate_now']:
                            optimization_text += "Closing selected programs:\n"
                            for proc in selected_processes:
                                try:
                                    # Skip if this is our own process
                                    if proc['pid'] == our_pid:
                                        optimization_text += f"! Skipped {proc['name']} (This is the optimizer program)\n"
                                        continue
                                        
                                    process = psutil.Process(proc['pid'])
                                    process.terminate()
                                    optimization_text += f"✓ Closed {proc['name']}\n"
                                except Exception as e:
                                    optimization_text += f"! Failed to close {proc['name']}: {e}\n"
                            optimization_text += "\n"
                        
                        optimization_text += "Additional Recommendations:\n"
                        optimization_text += "1. Use Task Manager to monitor resource usage\n"
                        optimization_text += "2. Consider uninstalling unused programs\n"
                        optimization_text += "3. Keep your system updated\n"
                        optimization_text += "4. Regular system maintenance is recommended\n"
                    else:
                        optimization_text += "No programs selected for optimization.\n"
                else:
                    optimization_text = "Optimization cancelled by user.\n"
            else:
                optimization_text = "No resource-intensive programs found.\n"
            
            self.optimization_info.setText(optimization_text)
            self.status_label.setText("Optimization analysis complete!")
            
        except Exception as e:
            error_msg = f"Error showing optimization dialog: {str(e)}"
            logging.error(error_msg)
            self.optimization_info.setText(error_msg)
            self.status_label.setText("Error during optimization!")

    def start_optimization(self):
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.status_label.setText("Starting optimization process...")
        self.optimization_info.setText("Optimization in progress...\nPlease wait while we optimize your system.")
        self.optimizer = OptimizationWorker()
        self.optimizer.optimization_complete.connect(self.optimization_finished)
        self.optimizer.progress_update.connect(self.update_status)
        self.optimizer.optimization_error.connect(self.handle_optimization_error)
        self.optimizer.start()
    
    def optimization_finished(self, results):
        try:
            # Update UI with optimization results
            status_text = "Optimization completed:\n\n"
            
            if results['power']:
                status_text += " Power settings optimized for performance\n"
            else:
                status_text += " Power settings optimization failed\n"
                
            if results['services']:
                status_text += " System services optimized\n"
            else:
                status_text += " System services optimization failed\n"
                
            if results['memory']:
                status_text += " Memory settings optimized\n"
            else:
                status_text += " Memory settings optimization failed\n"
                
            if results['process_priority']:
                status_text += " Process priorities optimized\n"
            else:
                status_text += " Process priorities optimization failed\n"
            
            status_text += f"\nOverall success rate: {results['success_percentage']:.1f}%"
            
            self.status_label.setText(status_text)
            self.progress.setVisible(False)
            self.scan_button.setEnabled(True)

        except Exception as e:
            logging.error(f"Error updating optimization results: {str(e)}")
            self.handle_optimization_error(f"Error displaying optimization results: {str(e)}")

    def handle_optimization_error(self, error_message):
        logging.error(f"Optimization error: {error_message}")
        self.status_label.setText(f"Optimization error: {error_message}")
        self.progress.setVisible(False)
        self.scan_button.setEnabled(True)

    def closeEvent(self, event):
        # Clean up any running threads
        if hasattr(self, 'scanner') and self.scanner.isRunning():
            self.scanner.wait()
        if hasattr(self, 'optimizer') and self.optimizer.isRunning():
            self.optimizer.wait()
        event.accept()

if __name__ == '__main__':
    # Set up logging first
    logging.basicConfig(level=logging.DEBUG,
                       format='%(asctime)s - %(levelname)s - %(message)s',
                       handlers=[logging.StreamHandler()])
    
    logging.info("Starting AI System Optimizer...")
    
    # Check if running as admin
    if not is_admin():
        logging.info("Not running as admin, requesting elevation...")
        run_as_admin()
    else:
        logging.info("Running with admin privileges")
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
