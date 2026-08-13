import cv2

image = cv2.imread("data/raw_images/3.jpg")

resized = cv2.resize(
    image,
    None,
    fx=2,
    fy=2,
    interpolation=cv2.INTER_CUBIC
)

cv2.imwrite("data/processed_images/3_resized_sample_food_image.jpg",resized)

print("Resized image saved.")
print("Original Shape:", image.shape)
print("Resized Shape:", resized.shape)