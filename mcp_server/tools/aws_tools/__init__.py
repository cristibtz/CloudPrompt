import importlib
import os
import logging

logger = logging.getLogger("aws_tools")

def register_aws_tools(mcp):
    """Auto-discover and register all AWS service tools"""
    current_dir = os.path.dirname(__file__)
    
    # Auto-discover all *_tools.py files
    for filename in os.listdir(current_dir):
        if filename.endswith('_tools.py') and not filename.startswith('__'):
            module_name = filename[:-3]  # Remove .py
            
            try:
                module = importlib.import_module(f'tools.aws_tools.{module_name}')
                if hasattr(module, 'register_tools'):
                    module.register_tools(mcp)
                    logger.info(f"✅ Registered {module_name}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to load {module_name}: {e}")
    
    logger.info("🚀 All AWS tools registered")