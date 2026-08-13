import cv2

image = cv2.imread("data/raw_images/3.jpg")

gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)

binary = cv2.adaptiveThreshold(
    gray,
    255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    11,
    2
)

cv2.imshow("binary Image",binary)
cv2.waitKey(0)
cv2.destroyAllWindows()

cv2.imwrite("data/processed_images/3_threshold_image.jpg",binary)

print("Thresholded image saved.")