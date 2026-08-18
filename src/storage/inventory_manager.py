import json
import os
from datetime import datetime


class InventoryManager:
    def __init__(self, inventory_file="data/inventory/inventory.json"):
        self.inventory_file = inventory_file
        os.makedirs(
            os.path.dirname(self.inventory_file),
            exist_ok=True
        )
        if not os.path.exists(self.inventory_file):
            with open(self.inventory_file, "w") as file:
                json.dump([], file)

    def load_inventory(self):
        with open(self.inventory_file, "r") as file:
            return json.load(file)

    def save_inventory(self, inventory):
        with open(self.inventory_file, "w") as file:
            json.dump(inventory,file,indent=4)

    def add_product(self, product_data):
        inventory = self.load_inventory()
        product_id = len(inventory) + 1
        record = {
            "id": product_id,
            "created_at": datetime.now().isoformat(),
            **product_data
        }

        inventory.append(record)
        self.save_inventory(inventory)
        return record
    
    def get_all_products(self):
        return self.load_inventory()
    
    def search_by_name(self, product_name):
        inventory = self.load_inventory()
        results = []
        for product in inventory:
            if product_name.lower() in product["product_name"].lower():
                results.append(product)
        
        return results
    
    def search_by_ingredient(self, ingredient):
        inventory = self.load_inventory()
        results = []
        for product in inventory:
            ingredients = product.get("ingredients",[])
            
            for item in ingredients:
                if ingredient.lower() in item.lower():
                    results.append(product)
                    break
            
        return results
    
    def search_by_allergen(self, allergen):
        inventory = self.load_inventory()
        results = []
        for product in inventory:
            allergens = product.get("allergens",[])
            
            for item in allergens:
                if allergen.lower() in item.lower():
                    results.append(product)
                    break
                
        return results
    
    def search_by_nutrition(self, nutrient):
        inventory = self.load_inventory()
        results = []
        
        for product in inventory:
            nutrition = product.get("nutrition",{})
            if nutrient in nutrition:
                results.append(product)
                
        return results