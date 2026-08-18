import hashlib
from pathlib import Path

def get_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_manifest():
    data_dir = Path("data/raw")
    files = [
        "sales_train_evaluation.csv",
        "calendar.csv",
        "sell_prices.csv",
        "sample_submission.csv"
    ]
    
    with open("data/raw/dataset_manifest.md", "w") as f:
        f.write("# Dataset Manifest\n\n")
        f.write("| Filename | SHA-256 Hash |\n")
        f.write("|---|---|\n")
        for filename in files:
            path = data_dir / filename
            if path.exists():
                file_hash = get_sha256(path)
                f.write(f"| {filename} | {file_hash} |\n")
            else:
                f.write(f"| {filename} | MISSING |\n")

if __name__ == "__main__":
    generate_manifest()
