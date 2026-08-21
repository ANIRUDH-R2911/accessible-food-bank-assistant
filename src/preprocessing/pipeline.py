import cv2

def preprocess_image(image_path):
    image = cv2.imread(image_path)
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
    return enhanced