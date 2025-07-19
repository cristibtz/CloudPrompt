import importlib
import os
import logging

logger = logging.getLogger("azure_tools")

def register_azure_tools(mcp):
    """Auto-discover and register all Azure service tools"""
    current_dir = os.path.dirname(__file__)
    
    # Auto-discover all *_tools.py files
    for filename in os.listdir(current_dir):
        if filename.endswith('_tools.py') and not filename.startswith('__'):
            module_name = filename[:-3]  # Remove .py
            
            try:
                module = importlib.import_module(f'tools.azure_tools.{module_name}')
                if hasattr(module, 'register_tools'):
                    module.register_tools(mcp)
                    logger.info(f"✅ Registered {module_name}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to load {module_name}: {e}")
    
    logger.info("🚀 All Azure tools registered")