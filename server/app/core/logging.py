import logging
import os

def setup_logging():
    # Step 1: Create a logs folder if it doesn't exist yet
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        
    # Step 2: The simple basicConfig exactly like we learned!
    logging.basicConfig(
        filename="logs/app.log", 
        level=logging.INFO, 
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s" 
    )
    
    logging.info("Centralized logging system initialized!")
