import os
import shutil
import argparse
from huggingface_hub import snapshot_download
from pathlib import Path

def download_from_hf(repo_id: str, local_dir: str = "."):
    """
    Downloads the pre-indexed data from Hugging Face.
    """
    print(f"\n🚀 Downloading data from Hugging Face repo: {repo_id}...")
    
    try:
        # Download the repository content
        # We allow patterns to make sure we only get what's needed if the repo is large
        snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            local_dir=local_dir,
            local_dir_use_symlinks=False
        )
        print(f"✅ Data downloaded and placed in: {local_dir}")
        print("Note: If the data was compressed, you might need to extract it manually if not handled by this script.")
        
    except Exception as e:
        print(f"❌ Error downloading data: {e}")
        print("\nMake sure the repo_id is correct and the repository is public (or you are logged in).")

def main():
    parser = argparse.ArgumentParser(description="Download pre-indexed documentation data from Hugging Face.")
    parser.add_argument(
        "--repo", 
        type=str, 
        default="Iruziky/docs-forai-data", 
        help="Hugging Face Dataset repo ID (e.g., 'username/repo-name')"
    )
    
    args = parser.parse_args()
    
    # Check if directories already exist to avoid accidental overwrites
    if os.path.exists("lancedb_data"):
        confirm = input("⚠️  Target directory (lancedb_data) already exists. Overwrite? (y/N): ")
        if confirm.lower() != 'y':
            print("Download cancelled.")
            return

    download_from_hf(args.repo)

if __name__ == "__main__":
    main()
