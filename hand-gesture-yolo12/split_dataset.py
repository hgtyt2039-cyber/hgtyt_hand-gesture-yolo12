import os
import shutil
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RAW_DIR = os.path.join(BASE_DIR, "dataset_raw_filtered")

OUT_DIR = os.path.join(BASE_DIR, "dataset_1000")

TRAIN_RATIO = 0.6
VAL_RATIO = 0.2
TEST_RATIO = 0.2

CLASSES = ["call", "fist", "palm", "peace", "stop", "like"]

IMG_EXT = [".jpg", ".jpeg", ".png"]

FOLDERS = [
    "images/train", "images/val", "images/test",
    "labels/train", "labels/val", "labels/test",
]

for folder in FOLDERS:
    os.makedirs(os.path.join(OUT_DIR, folder), exist_ok=True)

def is_image(file_name: str):
    ext = os.path.splitext(file_name)[1].lower()
    return ext in IMG_EXT

for cls in CLASSES:
    cls_folder = os.path.join(RAW_DIR, cls)

    if not os.path.isdir(cls_folder):
        print(f"[WARNING] Không tìm thấy thư mục lớp: {cls}")
        continue

    all_files = os.listdir(cls_folder)
    images = [f for f in all_files if is_image(f)]

    random.shuffle(images)

    total = len(images)
    train_cut = int(total * TRAIN_RATIO)
    val_cut = int(total * VAL_RATIO)

    train_files = images[:train_cut]
    val_files = images[train_cut:train_cut + val_cut]
    test_files = images[train_cut + val_cut:]

    print(f"\n======== {cls.upper()} ========")
    print(f"Total: {total}")
    print(f"Train = {len(train_files)}, Val = {len(val_files)}, Test = {len(test_files)}")

    for split, files in [
        ("train", train_files),
        ("val", val_files),
        ("test", test_files),
    ]:
        for img in files:
            img_src = os.path.join(cls_folder, img)

            base_name = os.path.splitext(img)[0]
            lbl_name = base_name + ".txt"
            lbl_src = os.path.join(cls_folder, lbl_name)

            img_dst = os.path.join(OUT_DIR, f"images/{split}", img)
            lbl_dst = os.path.join(OUT_DIR, f"labels/{split}", lbl_name)

            shutil.copy(img_src, img_dst)

            if os.path.exists(lbl_src):
                shutil.copy(lbl_src, lbl_dst)
            else:
                print(f"[WARNING] Thiếu label cho ảnh: {img_src}")

print("\n🎉 DONE — Đã chia dataset hoàn tất theo tỷ lệ 60/20/20!")
