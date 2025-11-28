"""
Run this script to delete old database and prepare for fresh start.
Place it in your project folder and run: python cleanup_and_setup.py
"""

import os
import sys

def clean_database():
    """Delete old database files to force recreation with new schema."""
    
    db_file = "edutrack.db"
    model_file = "model.pkl"
    
    print("🧹 Cleaning up old database files...\n")
    
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            print(f"✅ Deleted: {db_file}")
        except Exception as e:
            print(f"❌ Failed to delete {db_file}: {e}")
            return False
    
    if os.path.exists(model_file):
        try:
            os.remove(model_file)
            print(f"✅ Deleted: {model_file}")
        except Exception as e:
            print(f"⚠️  Could not delete {model_file}: {e}")
    
    print("\n✅ Cleanup complete!")
    print("\nNow restart the app:")
    print("   python -m streamlit run app.py")
    print("\n📝 A fresh database with all columns will be created automatically.")
    
    return True

if __name__ == "__main__":
    success = clean_database()
    sys.exit(0 if success else 1)
