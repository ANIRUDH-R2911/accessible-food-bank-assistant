import easyocr
import cv2

reader = easyocr.Reader(['en'])

original_image = cv2.imread("data/raw_images/1.jpg")

#gray_image = cv2.imread("data/processed_images/gray_sample_food_image.jpg")

#binary_image = cv2.imread("data/processed_images/threshold_image.jpg")

original_results = reader.readtext(original_image)

#gray_results = reader.readtext(gray_image)

#binary_results = reader.readtext(binary_image)

resized_image = cv2.imread("data/processed_images/resized_sample_food_image.jpg")

resized_results = reader.readtext(resized_image)

clahe_image = cv2.imread("data/processed_images/clahe_resized_image.jpg")

clahe_results = reader.readtext(clahe_image)

# Print results
print("=" * 50)
print("OCR RESULTS - ORIGINAL IMAGE")
print("=" * 50)

for result in original_results:
    print(result[1])
'''
print("\n")
print("=" * 50)
print("OCR RESULTS - GRAYSCALE IMAGE")
print("=" * 50)

for result in gray_results:
    print(result[1])
    
print("\n")
print("=" * 50)
print("OCR RESULTS - Binary IMAGE")
print("=" * 50)

for result in binary_results:
    print(result[1])
'''
print("=" * 50)
print("OCR RESULTS - RESIZED IMAGE")
print("=" * 50)

for result in resized_results:
    print(result[1])
    
print("=" * 50)
print("OCR RESULTS - CLAHE + RESIZE")
print("=" * 50)

for result in clahe_results:
    print(result[1])

