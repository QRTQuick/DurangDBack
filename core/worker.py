from PySide6.QtCore import QObject, Signal, QThread
import traceback
import sys

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    """
    started = Signal()
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(int)
    status = Signal(str)

class Worker(QObject):
    """
    Worker thread for handling long-running tasks.
    
    Attributes:
        signals (WorkerSignals): Signal interface for thread communication
        task (callable): Function to be executed in the thread
        args (tuple): Arguments for the task function
        kwargs (dict): Keyword arguments for the task function
    """
    
    def __init__(self, task_func, *args, **kwargs):
        super().__init__()
        self.signals = WorkerSignals()
        self.task = task_func
        self.args = args
        self.kwargs = kwargs
        self._is_running = True
        
    def run(self):
        """
        Initializes and executes the task thread
        """
        try:
            self.signals.started.emit()
            result = self.task(*self.args, **{**self.kwargs, 
                                            'progress_callback': self.signals.progress.emit,
                                            'status_callback': self.signals.status.emit})
            self.signals.result.emit(result)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        finally:
            self.signals.finished.emit()
            
    def stop(self):
        """
        Signals the worker to stop processing
        """
        self._is_running = False
            
def create_thread_worker(task_func, *args, **kwargs):
    """
    Factory function to create and setup a worker thread.
    
    Args:
        task_func (callable): The function to run in the thread
        *args: Arguments to pass to the task function
        **kwargs: Keyword arguments to pass to the task function
        
    Returns:
        tuple: (QThread, Worker) - The thread and worker objects
    """
    thread = QThread()
    worker = Worker(task_func, *args, **kwargs)
    worker.moveToThread(thread)
    
    # Connect signals
    thread.started.connect(worker.run)
    worker.signals.finished.connect(thread.quit)
    worker.signals.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    
    return thread, worker
