from PySide6.QtCore import QObject
from .worker import create_thread_worker

class ThreadManager(QObject):
    """
    Manages worker threads for the application.
    Ensures proper thread lifecycle and cleanup.
    """
    
    def __init__(self):
        super().__init__()
        self._active_threads = {}
        
    def start_worker(self, name, task_func, *args, 
                    on_start=None, on_result=None, on_error=None, 
                    on_finished=None, on_progress=None, on_status=None,
                    **kwargs):
        """
        Creates and starts a new worker thread.
        
        Args:
            name (str): Unique identifier for the thread
            task_func (callable): Function to run in the thread
            *args: Arguments for the task function
            on_start: Callback when thread starts
            on_result: Callback when thread produces a result
            on_error: Callback when thread encounters an error
            on_finished: Callback when thread finishes
            on_progress: Callback for progress updates
            on_status: Callback for status messages
            **kwargs: Keyword arguments for the task function
            
        Returns:
            tuple: (thread, worker) - The created thread and worker objects
        """
        # Clean up any existing thread with the same name
        self.stop_worker(name)
        
        # Create new thread and worker
        thread, worker = create_thread_worker(task_func, *args, **kwargs)
        
        # Connect optional callbacks
        if on_start:
            worker.signals.started.connect(on_start)
        if on_result:
            worker.signals.result.connect(on_result)
        if on_error:
            worker.signals.error.connect(on_error)
        if on_finished:
            worker.signals.finished.connect(on_finished)
        if on_progress:
            worker.signals.progress.connect(on_progress)
        if on_status:
            worker.signals.status.connect(on_status)
            
        # Store thread and worker
        self._active_threads[name] = (thread, worker)
        
        # Start the thread
        thread.start()
        
        return thread, worker
    
    def stop_worker(self, name):
        """
        Stops and cleans up a worker thread.
        
        Args:
            name (str): The identifier of the thread to stop
        """
        if name in self._active_threads:
            thread, worker = self._active_threads[name]
            worker.stop()
            thread.quit()
            thread.wait()
            del self._active_threads[name]
            
    def stop_all(self):
        """
        Stops all active worker threads.
        """
        names = list(self._active_threads.keys())
        for name in names:
            self.stop_worker(name)
            
    def is_running(self, name):
        """
        Checks if a named thread is running.
        
        Args:
            name (str): The identifier of the thread
            
        Returns:
            bool: True if the thread is running, False otherwise
        """
        return name in self._active_threads