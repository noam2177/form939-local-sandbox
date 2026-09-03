from __future__ import annotations

import csv
import random
from pathlib import Path

def generate_valid_id() -> str:
    """Generate a valid 9-digit Israeli ID."""
    while True:
        num = "".join(str(random.randint(0, 9)) for _ in range(9))
        total = 0
        for i, digit in enumerate(num):
            val = int(digit) * (1 if i % 2 == 0 else 2)
            total += val if val < 10 else val - 9
        if total % 10 == 0:
            return num

def apply_ocr_noise(id_str: str, noise_type: str) -> str:
    """Apply common OCR noise to an ID string."""
    if noise_type == "missing_zero" and id_str.startswith("0"):
        return id_str[1:]
    elif noise_type == "spaces":
        return " ".join(list(id_str))
    elif noise_type == "rtl_marks":
        return f"\u200e{id_str}\u200f"
    elif noise_type == "dash":
        return f"{id_str[:1]}-{id_str[1:]}"
    elif noise_type == "hebrew_confusion":
        # Confuse 0 with ם (Mem sofit) and 1 with ן (Nun sofit)
        noisy = id_str.replace("0", "ם").replace("1", "ן")
        return noisy
    elif noise_type == "missing_completely":
        return ""
    return id_str

def generate_synthetic_dataset(num_samples: int, output_dir: Path, gt_csv_path: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    gt_csv_path.parent.mkdir(parents=True, exist_ok=True)

    noise_types = ["none", "missing_zero", "spaces", "rtl_marks", "dash", "hebrew_confusion", "missing_completely"]
    
    gt_rows = []
    
    for i in range(num_samples):
        filename = f"synthetic_sample_{i:03d}"
        
        principal_id = generate_valid_id()
        attorney_id = generate_valid_id()
        
        # Force one to start with 0 for testing "missing_zero"
        if random.choice([True, False]):
            principal_id = "0" + principal_id[1:]
            # fix luhn
            while True:
                total = 0
                for j, digit in enumerate(principal_id):
                    val = int(digit) * (1 if j % 2 == 0 else 2)
                    total += val if val < 10 else val - 9
                if total % 10 == 0:
                    break
                principal_id = "0" + "".join(str(random.randint(0, 9)) for _ in range(8))

        principal_noise = random.choice(noise_types)
        attorney_noise = random.choice(noise_types)
        
        principal_text = apply_ocr_noise(principal_id, principal_noise)
        attorney_text = apply_ocr_noise(attorney_id, attorney_noise)
        
        principal_hw = random.choice([True, False])
        attorney_hw = random.choice([True, False])
        
        text = f"""=== SCAN / OCR DUMP — טופס 939 ייפוי כוח ===
<RTL>  מדינת ישראל  |  רשות האוכלוסין

נותן ההרשאה / מייפה כוח / PRINCIPAL:
  ת.ז: {principal_text}
  מודפס (לא בכתב יד) - {'FALSE' if principal_hw else 'TRUE'}
  בכתב יד: {'כן' if principal_hw else 'לא'}

מקבל ההרשאה / מיופה כוח / ATTORNEY IN FACT:
  ת.ז: {attorney_text}
  בכתב יד / handwritten = {'TRUE' if attorney_hw else 'FALSE'}

=== END OCR ===
"""
        (output_dir / f"{filename}.txt").write_text(text, encoding="utf-8")
        
        if principal_noise == "missing_completely":
            principal_id = ""
        if attorney_noise == "missing_completely":
            attorney_id = ""

        gt_rows.append({
            "Filename": filename,
            "principal.value": principal_id,
            "principal.is_handwritten": str(principal_hw).lower() if principal_id else "false",
            "attorney_in_fact.value": attorney_id,
            "attorney_in_fact.is_handwritten": str(attorney_hw).lower() if attorney_id else "false",
        })

    with open(gt_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["Filename", "principal.value", "principal.is_handwritten", "attorney_in_fact.value", "attorney_in_fact.is_handwritten"])
        writer.writeheader()
        writer.writerows(gt_rows)
        
    print(f"Generated {num_samples} samples in {output_dir}")
    print(f"Ground truth saved to {gt_csv_path}")

if __name__ == "__main__":
    generate_synthetic_dataset(
        num_samples=20, 
        output_dir=Path("data/synthetic_inputs"), 
        gt_csv_path=Path("data/gold/synthetic_ground_truth.csv")
    )
