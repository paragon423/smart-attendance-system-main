import os
import pickle
import numpy as np
from data import init_db, save_staff_face

# Define the path where your old .pkl files are stored
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OLD_DB_PATH = os.path.join(BASE_DIR, "database", "department_data")

def run_migration():
    print("--- Starting Migration ---")
    
    # 1. Initialize the new SQLite database
    init_db()
    
    if not os.path.exists(OLD_DB_PATH):
        print(f"Error: Could not find old data at {OLD_DB_PATH}")
        return

    # 2. Loop through every department folder (e.g., CSE_A, ECE_B)
    departmentes = [d for d in os.listdir(OLD_DB_PATH) if os.path.isdir(os.path.join(OLD_DB_PATH, d))]
    
    total_migrated = 0

    for department in departmentes:
        pkl_path = os.path.join(OLD_DB_PATH, department, f"{department}_db.pkl")
        
        if os.path.exists(pkl_path):
            print(f"\nProcessing department: {department}")
            
            try:
                # 3. Open the old pickle file
                with open(pkl_path, 'rb') as f:
                    old_data = pickle.load(f) # Format: {staff_id: embedding_vector}
                
                # 4. Insert each staff member into the new SQL database
                for staff_id, embedding in old_data.items():
                    success = save_staff_face(staff_id, department, embedding)
                    if success:
                        print(f"  [OK] Migrated: {staff_id}")
                        total_migrated += 1
                    else:
                        print(f"  [FAILED] Could not migrate: {staff_id}")
            
            except Exception as e:
                print(f"  [ERROR] Problem reading {pkl_path}: {e}")
        else:
            print(f"\nSkipping {department}: No .pkl file found.")

    print(f"\n--- Migration Finished! ---")
    print(f"Total staff moved to SQL: {total_migrated}")

if __name__ == "__main__":
    run_migration()