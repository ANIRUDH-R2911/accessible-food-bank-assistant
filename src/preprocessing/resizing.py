import cv2

# Load image
image = cv2.imread(
    "data/raw_images/1.jpg"
)

# Resize 2x
resized = cv2.resize(
    image,
    None,
    fx=2,
    fy=2,
    interpolation=cv2.INTER_CUBIC
)

# Save image
cv2.imwrite(
    "data/processed_images/resized_sample_food_image.jpg",
    resized
)

print("Resized image saved.")
print("Original Shape:", image.shape)
print("Resized Shape:", resized.shape)