import os
import random

import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def generate_random_photos(count: int = 10, size: tuple = (384, 384)) -> list[np.ndarray]:
    images = []
    for _ in range(count):
        img = np.zeros((*size, 3), dtype=np.uint8)
        for _ in range(random.randint(3, 8)):
            color = tuple(random.randint(0, 255) for _ in range(3))
            x1, y1 = random.randint(0, size[1]), random.randint(0, size[0])
            x2, y2 = random.randint(0, size[1]), random.randint(0, size[0])
            if random.random() < 0.5:
                cv2.rectangle(img, (min(x1, x2), min(y1, y2)), (max(x1, x2), max(y1, y2)), color, -1)
            else:
                r = random.randint(10, min(size) // 3)
                cv2.circle(img, (x1, y1), r, color, -1)
        noise = np.random.randint(0, 30, (*size, 3), dtype=np.uint8)
        img = cv2.addWeighted(img, 0.8, noise, 0.2, 0)
        images.append(img)
    return images


def generate_noise_images(count: int = 10, size: tuple = (384, 384)) -> list[np.ndarray]:
    images = []
    for _ in range(count):
        noise_type = random.choice(['gaussian', 'salt_pepper', 'poisson'])
        if noise_type == 'gaussian':
            mean = random.uniform(100, 200)
            sigma = random.uniform(30, 80)
            noise = np.random.normal(mean, sigma, (*size, 3)).astype(np.uint8)
        elif noise_type == 'salt_pepper':
            noise = np.random.randint(0, 256, (*size, 3), dtype=np.uint8)
            mask = np.random.random((*size, 3))
            noise[mask < 0.3] = 0
            noise[mask > 0.7] = 255
        else:
            noise = np.random.poisson(lam=random.randint(80, 180), size=(*size, 3)).astype(np.uint8)
        images.append(np.clip(noise, 0, 255).astype(np.uint8))
    return images


def generate_uniform_images(count: int = 10, size: tuple = (384, 384)) -> list[np.ndarray]:
    images = []
    for _ in range(count):
        color = random.randint(0, 255)
        noise_level = random.uniform(0, 5)
        img = np.full((*size, 3), color, dtype=np.uint8)
        if noise_level > 0:
            noise = np.random.randint(0, noise_level + 1, (*size, 3), dtype=np.uint8)
            img = cv2.addWeighted(img, 1.0, noise, 1.0, 0) if CV2_AVAILABLE else np.clip(img.astype(np.int16) + noise.astype(np.int16), 0, 255).astype(np.uint8)
        images.append(img)
    return images


def generate_non_ultrasound_dataset(output_dir: str, count_per_type: int = 10):
    os.makedirs(output_dir, exist_ok=True)
    photos = generate_random_photos(count_per_type)
    noises = generate_noise_images(count_per_type)
    uniforms = generate_uniform_images(count_per_type)
    all_images = photos + noises + uniforms
    labels = (['foto'] * count_per_type) + (['ruido'] * count_per_type) + (['uniforme'] * count_per_type)
    saved = 0
    for i, (img, label) in enumerate(zip(all_images, labels, strict=False)):
        fname = f"no_ecografia_{label}_{i+1:03d}.jpg"
        fpath = os.path.join(output_dir, fname)
        if PIL_AVAILABLE:
            Image.fromarray(img).save(fpath, quality=95)
        elif CV2_AVAILABLE:
            cv2.imwrite(fpath, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        saved += 1
    return saved


if __name__ == "__main__":
    base = "C:\\Users\\Miscar\\Desktop\\Nueva carpeta\\historial\\Backend\\Microservicio_IA\\datasets_pathology"
    train_noeco = os.path.join(base, "train", "no_ecografia")
    val_noeco = os.path.join(base, "validation", "no_ecografia")
    train_saved = generate_non_ultrasound_dataset(train_noeco, count_per_type=10)
    val_saved = generate_non_ultrasound_dataset(val_noeco, count_per_type=5)
    print(f"Generadas {train_saved} imágenes train/no_ecografia/ + {val_saved} validation/no_ecografia/")
