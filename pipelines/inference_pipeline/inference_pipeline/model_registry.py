import logging
import threading
import time
import psutil
from typing import Any, Callable, Dict, List, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)

class ModelRegistryService:
    """
    A service that manages loaded models and provides efficient caching.
    
    This class implements a thread-safe LRU (Least Recently Used) caching mechanism
    for language models to avoid loading the same model multiple times and to
    efficiently manage memory usage.
    
    Attributes:
        _models (Dict): Dictionary mapping model_id to model objects
        _lru (List): List tracking the LRU order of models
        _max_models (int): Maximum number of models to keep in memory
        _lock (threading.Lock): Thread safety lock
        _last_access_time (Dict): Dictionary tracking when each model was last accessed
        _memory_check_interval (int): Interval in seconds to check memory pressure
        _last_memory_check (float): Timestamp of the last memory check
        _max_memory_percent (float): Maximum memory usage percentage before evicting models
    """
    
    def __init__(
        self, 
        max_models: int = 3, 
        memory_check_interval: int = 60,
        max_memory_percent: float = 85.0
    ):
        """
        Initialize the ModelRegistryService.
        
        Args:
            max_models (int): Maximum number of models to keep in memory
            memory_check_interval (int): Interval in seconds to check memory pressure
            max_memory_percent (float): Maximum memory usage percentage before evicting models
        """
        self._models = {}  # model_id -> model
        self._lru = []  # LRU queue
        self._max_models = max_models
        self._lock = threading.Lock()  # Thread safety
        self._last_access_time = {}  # model_id -> last access time
        self._memory_check_interval = memory_check_interval
        self._last_memory_check = 0
        self._max_memory_percent = max_memory_percent
        
    def get_model(
        self, 
        model_id: str, 
        loader_fn: Callable[[], Any]
    ) -> Any:
        """
        Get a model from the registry, loading it if necessary.
        
        Uses the provided loader_fn if the model is not already loaded.
        Also performs memory management by checking memory pressure and
        potentially unloading least recently used models.
        
        Args:
            model_id (str): Unique identifier for the model
            loader_fn (Callable): Function to call to load the model if not cached
            
        Returns:
            Any: The requested model
        """
        # Check memory pressure periodically
        current_time = time.time()
        if current_time - self._last_memory_check > self._memory_check_interval:
            self._check_memory_pressure()
            self._last_memory_check = current_time
            
        with self._lock:
            if model_id in self._models:
                # Update LRU and last access time
                self._lru.remove(model_id)
                self._lru.append(model_id)
                self._last_access_time[model_id] = time.time()
                logger.info(f"Model {model_id} retrieved from cache")
                return self._models[model_id]
            
            # Load the model
            logger.info(f"Loading model {model_id} (not found in cache)")
            model = loader_fn()
            
            # Evict least recently used model if needed
            if len(self._models) >= self._max_models:
                self._unload_least_used_model()
            
            # Add new model
            self._models[model_id] = model
            self._lru.append(model_id)
            self._last_access_time[model_id] = time.time()
            return model
    
    def _check_memory_pressure(self):
        """
        Check if system memory is under pressure and unload models if necessary.
        """
        memory_info = psutil.virtual_memory()
        memory_percent = memory_info.percent
        
        logger.debug(f"Memory usage: {memory_percent:.1f}%")
        
        if memory_percent > self._max_memory_percent:
            logger.warning(f"Memory pressure detected ({memory_percent:.1f}% used, threshold: {self._max_memory_percent:.1f}%)")
            with self._lock:
                while self._lru and memory_percent > self._max_memory_percent:
                    self._unload_least_used_model()
                    # Check memory again
                    memory_info = psutil.virtual_memory()
                    memory_percent = memory_info.percent
    
    def _unload_least_used_model(self):
        """
        Unload the least recently used model.
        
        This method should be called with the lock acquired.
        """
        if not self._lru:
            return
            
        lru_model_id = self._lru.pop(0)
        logger.info(f"Unloading least recently used model: {lru_model_id}")
        
        # Get the model to unload
        model = self._models[lru_model_id]
        
        # If it's a torch model, explicitly move it to CPU and clear CUDA cache
        if hasattr(model, 'to') and callable(model.to):
            model.to('cpu')
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
        # Remove from registry
        del self._models[lru_model_id]
        del self._last_access_time[lru_model_id]
        
    def preload_model(self, model_id: str, loader_fn: Callable[[], Any]) -> None:
        """
        Preload a model into the registry.
        
        This is useful for models that are expected to be used frequently.
        
        Args:
            model_id (str): Unique identifier for the model
            loader_fn (Callable): Function to call to load the model
        """
        logger.info(f"Preloading model {model_id}")
        self.get_model(model_id, loader_fn)
        
    def clear(self) -> None:
        """
        Clear all models from the registry.
        """
        with self._lock:
            for model_id in list(self._models.keys()):
                model = self._models[model_id]
                
                # If it's a torch model, explicitly move it to CPU and clear CUDA cache
                if hasattr(model, 'to') and callable(model.to):
                    model.to('cpu')
                
                del self._models[model_id]
                
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            self._lru = []
            self._last_access_time = {}
            logger.info("Model registry cleared")
            
    def get_stats(self) -> Dict:
        """
        Get statistics about the model registry.
        
        Returns:
            Dict: Dictionary with statistics about the model registry
        """
        with self._lock:
            return {
                "models_loaded": len(self._models),
                "max_models": self._max_models,
                "loaded_models": list(self._models.keys()),
                "lru_order": self._lru.copy(),
                "memory_usage_percent": psutil.virtual_memory().percent,
                "max_memory_percent": self._max_memory_percent
            }
