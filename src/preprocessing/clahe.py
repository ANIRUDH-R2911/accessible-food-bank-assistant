import cv2

image = cv2.imread("data/raw_images/3.jpg")

gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)

resized = cv2.resize(
    gray,
    None,
    fx=2,
    fy=2,
    interpolation=cv2.INTER_CUBIC
)

clahe = cv2.createCLAHE(clipLimit=2.0,tileGridSize=(8, 8))

enhanced = clahe.apply(resized)

cv2.imwrite("data/processed_images/3_clahe_resized_image.jpg",enhanced)

print("CLAHE image saved.")