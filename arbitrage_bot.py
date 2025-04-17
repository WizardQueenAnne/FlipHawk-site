import random

def generate_simulated_opportunities(subcategories):
    """
    Generate simulated arbitrage opportunities for demonstration purposes.
    This is used when no real arbitrage opportunities are found.
    """
    simulated = []
    
    product_templates = {
        "Laptops": [
            {"name": "Dell XPS 13 9310 13.4 inch FHD+ Laptop", "low": 699, "high": 999},
            {"name": "MacBook Air M1 8GB RAM 256GB SSD", "low": 749, "high": 999},
            {"name": "Lenovo ThinkPad X1 Carbon Gen 9", "low": 899, "high": 1349},
            {"name": "ASUS ROG Zephyrus G14 Gaming Laptop", "low": 1099, "high": 1499}
        ],
        "Smartphones": [
            {"name": "iPhone 13 Pro 128GB Graphite Unlocked", "low": 699, "high": 899},
            {"name": "Samsung Galaxy S21 Ultra 5G 128GB", "low": 649, "high": 899},
            {"name": "Google Pixel 6 Pro 128GB", "low": 499, "high": 749},
            {"name": "OnePlus 9 Pro 5G 256GB", "low": 599, "high": 799}
        ],
        "Pokémon": [
            {"name": "Charizard VMAX Rainbow Rare 074/073", "low": 149, "high": 249},
            {"name": "Booster Box Pokémon Brilliant Stars Sealed", "low": 99, "high": 159},
            {"name": "Pikachu VMAX Rainbow Rare 188/185", "low": 129, "high": 219},
            {"name": "Ancient Mew Sealed Promo Card", "low": 39, "high": 89}
        ],
        "Magic: The Gathering": [
            {"name": "Liliana of the Veil Innistrad Mythic", "low": 49, "high": 89},
            {"name": "Jace, the Mind Sculptor Worldwake", "low": 99, "high": 189},
            {"name": "Tarmogoyf Modern Horizons 2", "low": 29, "high": 59},
            {"name": "Mana Crypt Eternal Masters", "low": 159, "high": 259}
        ],
        "Yu-Gi-Oh!": [
            {"name": "Blue-Eyes White Dragon 1st Edition", "low": 79, "high": 149},
            {"name": "Dark Magician Girl 1st Edition", "low": 69, "high": 119},
            {"name": "Accesscode Talker Prismatic Secret Rare", "low": 59, "high": 99},
            {"name": "Ash Blossom & Joyous Spring Ultra Rare", "low": 29, "high": 49}
        ],
        "Sneakers": [
            {"name": "Nike Air Jordan 1 Retro High OG", "low": 189, "high": 299},
            {"name": "Adidas Yeezy Boost 350 V2", "low": 219, "high": 349},
            {"name": "Nike Dunk Low Retro White Black", "low": 99, "high": 179},
            {"name": "New Balance 550 White Green", "low": 89, "high": 159}
        ],
        "Denim": [
            {"name": "Levi's 501 Original Fit Jeans Vintage", "low": 45, "high": 99},
            {"name": "Vintage Wrangler Cowboy Cut Jeans", "low": 39, "high": 85},
            {"name": "Lee Riders Vintage High Waisted Jeans", "low": 49, "high": 110},
            {"name": "Carhartt Double Knee Work Jeans", "low": 55, "high": 95}
        ],
        "Vintage Toys": [
            {"name": "Star Wars Vintage Kenner Action Figure", "low": 29, "high": 89},
            {"name": "Transformers G1 Optimus Prime", "low": 89, "high": 249},
            {"name": "Original Nintendo Game Boy", "low": 59, "high": 129},
            {"name": "Vintage Barbie Doll 1970s", "low": 49, "high": 119}
        ]
    }
    
    # Default products if specific category not found
    default_products = [
        {"name": "Vintage Collection Rare Item", "low": 79, "high": 149},
        {"name": "Limited Edition Collectible", "low": 49, "high": 119},
        {"name": "Rare Discontinued Model", "low": 99, "high": 199},
        {"name": "Sealed Original Package Item", "low": 59, "high": 129}
    ]
    
    # Generate 5-10 opportunities for the subcategories
    for subcategory in subcategories:
        # Find appropriate product templates
        templates = None
        for key in product_templates:
            if key.lower() in subcategory.lower() or subcategory.lower() in key.lower():
                templates = product_templates[key]
                break
        
        if not templates:
            templates = default_products
        
        # Create 1-3 opportunities for this subcategory
        for _ in range(random.randint(1, 3)):
            template = random.choice(templates)
            
            # Add some randomness to the prices
            buy_price = template["low"] * random.uniform(0.9, 1.1)
            sell_price = template["high"] * random.uniform(0.9, 1.1)
            
            # Calculate profit metrics
            profit = sell_price - buy_price
            profit_percentage = (profit / buy_price) * 100
            
            # Generate random confidence score
            confidence = random.randint(70, 95)
            
            # Create opportunity
            opportunity = {
                "title": template["name"],
                "buyPrice": round(buy_price, 2),
                "sellPrice": round(sell_price, 2),
                "buyLink": "https://www.ebay.com/sch/i.html?_nkw=" + template["name"].replace(" ", "+"),
                "sellLink": "https://www.ebay.com/sch/i.html?_nkw=" + template["name"].replace(" ", "+") + "&_sop=16",
                "profit": round(profit, 2),
                "profitPercentage": round(profit_percentage, 2),
                "confidence": confidence,
                "subcategory": subcategory
            }
            
            simulated.append(opportunity)
    
    # Sort by profit percentage and return
    return sorted(simulated, key=lambda x: -x["profitPercentage"])

def run_arbitrage_scan(subcategories):
    """
    This is the function that app.py is trying to import and use.
    Simply calls generate_simulated_opportunities for now.
    In the future, this could be expanded to do real arbitrage scanning.
    """
    return generate_simulated_opportunities(subcategories)

if __name__ == "__main__":
    # Test the function with some subcategories
    test_subcategories = ["Pokémon", "Sneakers", "Magic: The Gathering"]
    results = run_arbitrage_scan(test_subcategories)
    print(f"Found {len(results)} arbitrage opportunities:")
    for i, opportunity in enumerate(results, 1):
        print(f"{i}. {opportunity['title']}")
        print(f"   Buy: ${opportunity['buyPrice']:.2f} | Sell: ${opportunity['sellPrice']:.2f}")
        print(f"   Profit: ${opportunity['profit']:.2f} ({opportunity['profitPercentage']:.1f}%)")
        print(f"   Confidence: {opportunity['confidence']}%")
        print(f"   Subcategory: {opportunity['subcategory']}")
        print()
