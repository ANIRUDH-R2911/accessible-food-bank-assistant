import cv2

image = cv2.imread("data/raw_images/1.jpg")
output_path = "data/processed_images/gray_sample_food_image.jpg"

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

cv2.imwrite(output_path, gray)

cv2.waitKey(0)
cv2.destroyAllWindows()